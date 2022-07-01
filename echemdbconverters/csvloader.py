r"""
Converter for CSV files (https://datatracker.ietf.org/doc/html/rfc4180)
which consist of a single header line containing the column names
and rows with comma separated data.

The CSV object has the following properties:
::TODO: Add examples for the following functions
* a DataFrame
* the column names
* the header contents
* the number of header lines
* metadata

Special converters for non standard CSV files can be called:

::TODO: Add example

"""
# ********************************************************************
#  This file is part of echemdb-converters.
#
#        Copyright (C) 2022 Albert Engstfeld
#        Copyright (C) 2022 Johannes Hermann
#        Copyright (C) 2022 Julian Rüth
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
from functools import cache


class CSVloader:
    r"""Reads a CSV, where the first line contains the column names
    and the following lines comma separated data.

    EXAMPLES::

        >>> from io import StringIO
        >>> file = StringIO(r'''a,b
        ... 0,0
        ... 1,1''')
        >>> csv = CSVloader(file)
        >>> csv.df
           a  b
        0  0  0
        1  1  1

    A list of names describing the columns::

        >>> csv.column_names
        ['a', 'b']

    More specific converters can be selected::
    TODO:: Add example with csv.get_device('device')(file)

    """

    def __init__(self, file, metadata=None):
        self._file = file.read()
        self._metadata = metadata or {}

    @property
    def file(self):
        r"""A file like object.

        EXAMPLES::
            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> type(csv.file)
            <class '_io.StringIO'>

        """
        from io import StringIO

        return StringIO(self._file)

    @staticmethod
    def get_loader(device=None):
        r"""
        Calls a specific `loader` based on a given device.
        """
        # import here to avoid cyclical dependencies
        # TODO: Implement the following converters
        # TODO: from .thiolab_labview_converter import ThiolabLabviewConverter
        # TODO: from .genericcsvconverter import GenericCsvConverter
        # TODO: from .eclabconverter import EclabConverter
        # The following dict is a placeholder for further specific converters.
        # They hare here to get an idea what this function should do. These are currently not tested.
        from .eclabloader import ECLabLoader

        devices = {  #'generic' : GenericCsvLoader, # Generic CSV converter
            "eclab": ECLabLoader,  # Biologic-EClab device
            #'Thiolab Labview' : ThiolabLabviewLoader, # Labview data recorder formerly used in the thiolab
        }

        if device in devices:
            return devices[device]

        raise KeyError(f"Device wth name '{device}' is unknown to the loader'.")

    @property
    def df(self):
        r"""
        A pandas dataframe of the CSV.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.df
               a  b
            0  0  0
            1  1  1

        """
        import pandas as pd

        return pd.read_csv(self.file, header=self.header_lines)

    @property
    def header(self):
        r"""
        The header of the CVS file
        (column names excluded).

        A standard CSV file does not have a header.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.header
            []

        """
        lines = self.file.readlines()
        return [lines[_] for _ in range(self.header_lines)]

    @property
    @cache
    def column_names(self):
        r"""List of column names describing the tabulated data.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.column_names
            ['a', 'b']

        """
        return self.df.columns.to_list()

    @property
    def header_lines(self):
        r"""
        The number of header lines of a CSV without column names.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.header_lines
            0

        """
        return 0

    @property
    def metadata(self):
        r"""
        Metadata constructed from input metadata and the CSV header.
        A simple CSV does not have any metadata in the header.
        """
        return self._metadata.copy()

    @property
    def schema(self, fields=None):
        """
        A frictionless `Schema` object, including a `Fields` object
        describing the columns.
        The fields can be provided or will be extracted from the metadata,
        where they should be located in `figure_description.schema.fields'.

        TODO:: If the fields are not provided they could be constructed from the the column names.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
            >>> csv = CSVloader(file, metadata)
            >>> csv.schema
            {'fields': [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema

        schema = Schema(fields=fields or self._create_fields())

        return self._validated_schema(schema)

    def _create_fields(self):
        try:
            fields = self.metadata["figure description"]['schema']["fields"]
        except:
            raise Exception(
                "`fields` are not specified in the metadata `figure description`."
            )
        return fields

    def _validated_schema(self, schema):
        if not len(self.column_names) == len(schema.field_names):
            raise Exception(f"The number of columns ({len(self.column_names)}) does not match the number of fields ({len(schema.field_names)}) in the schema.")

        for name in self.column_names:
            if not name in schema.field_names:
                raise KeyError(
                    f"The schema does not have a description for the column with name '{name}'."
                )

        return schema