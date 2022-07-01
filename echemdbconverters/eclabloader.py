r"""
Converts MPT files recorded with the EC-Lab software from BioLogic for BioLogic potentiostats.
"""
# ********************************************************************
#  This file is part of echemdb-converters.
#
#        Copyright (C) 2022 Albert Engstfeld
#        Copyright (C) 2022 Johannes Hermann
#
#  echemdb-converters is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  echemdb-converters is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with echemdb-converters. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************


from .csvloader import CSVloader

biologic_fields = [
    {'name': 'mode',
    },
    {'name': 'ox/red',
    },
    {'name': 'error',
    },
    {'name': 'control changes',
    },
    {'name': 'counter inc.',
    },
    {'name': 'ox/red',
    },
    {'name': 'time/s',
    'unit': 's',
    },
    {'name':'control/V',
    'unit': 'V',
    },
    {'name': 'Ewe',
     'unit': 'V',
     },
    {'name': '<I>/mA',
     'unit': 'mA',
    },
    {'name': 'cycle number',
    },
    {'name': '(Q-Qo)/C',
    'unit': 'C',
    },
    {'name': 'P/W',
     'unit': 'W',
    },
    {'name': 'Unnamed : 13', # It seems that there is an unnamed column in the csv where the number reflects the number of columns.
    },
    ]

class ECLabLoader(CSVloader):
    r"""Loads BioLogic EC-Lab MPT files.
    The following examples are based on the general structure of MPT files.

    EXAMPLES::

        >>> from io import StringIO
        >>> file = StringIO('''EC-Lab ASCII FILE
        ... Nb header lines : 6
        ...
        ... Device metadata : some metadata
        ...
        ... mode\ttime/s\tcontrol/V
        ... 2\t0\t0
        ... 2\t1\t1,4
        ... ''')
        >>> from .csvloader import CSVloader
        >>> csv = CSVloader.get_loader('eclab')(file)
        >>> csv.df
           mode  time/s  control/V
        0     2       0        0.0
        1     2       1        1.4

        >>> csv.header
        ['EC-Lab ASCII FILE\n', 'Nb header lines : 6\n', '\n', 'Device metadata : some metadata\n', '\n']

        >>> csv.column_names
        ['mode', 'time/s', 'control/V']

    """

    @property
    def header_lines(self):
        r"""The number of header lines of an EC-Lab MPT file without column names.
        The value is determined from the number of header lines provided
        in the MPT file (in which the column names are included.)
        The value varies depending on the options selected in EC-Lab.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''EC-Lab ASCII FILE
            ... Nb header lines : 6
            ...
            ... Device metadata : some metadata
            ...
            ... mode    time/s  control/V
            ... 2   0   0
            ... 2   1   1,4
            ... ''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader.get_loader('eclab')(file)
            >>> csv.header_lines
            5

        """
        matches = []

        for line in self.file.readlines():
            import re

            match = re.findall(
                r"(?P<headerlines>Nb header lines) *\: *(?P<value>-?\d+\.?\d*)",
                str(line),
                re.IGNORECASE,
            )

            if match:
                matches.append(match)

        header_lines = int(matches[0][0][1])
        # The counter should be reset, otherwise pd.read_csv() is not able to read the file
        return header_lines - 1

    @property
    def df(self):
        r"""A pandas dataframe extracted from an EC-Lab MPT file.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO('''EC-Lab ASCII FILE
            ... Nb header lines : 6
            ...
            ... Device metadata : some metadata
            ...
            ... mode\ttime/s\tcontrol/V
            ... 2\t0\t0
            ... 2\t1\t1,4
            ... ''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader.get_loader('eclab')(file)
            >>> csv.df
               mode  time/s  control/V
            0     2       0        0.0
            1     2       1        1.4

        """
        import pandas as pd

        return pd.read_csv(
            self.file,
            sep="\t",
            header=self.header_lines,
            decimal=",",
            encoding="latin1",
            skip_blank_lines=False,
        )

    @property
    def schema(self):
        """
        ECLab schema
        """
        from frictionless import Schema

        metadata = self._metadata.copy()

        metadata.setdefault('figure description', {})

        if not metadata['figure description']:
            metadata['figure description'].setdefault('schema', {})

        if not metadata['figure description']['schema']:
            metadata['figure description']['schema'].setdefault('fields', [])

        if not metadata['figure description']['schema']['fields']:
            schema = Schema(fields=self._create_fields())

        else:
            schema = Schema(fields=metadata['figure description']['schema']['fields'])
            self._validate_schema(schema)

        return schema

    def _create_fields(self):

        fields = []

        for item in biologic_fields:
            for name in self.column_names:
                if name == item['name']:
                    fields.append(item)

        return fields
