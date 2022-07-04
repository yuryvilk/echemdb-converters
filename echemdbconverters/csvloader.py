r"""
Loader for CSV files (https://datatracker.ietf.org/doc/html/rfc4180)
which consist of a single header line containing the column (field)
names and rows with comma separated values.

In pandas the names of the columns are referred to as `column_names`,
whereas in frictionless datapackages the column names are called `fields`.
The latter contain additional information such as the type of data,
a title or a description.

The CSV object has the following properties:
::TODO: Add examples for the following functions
* a DataFrame
* the column names
* the header contents
* the number of header lines
* metadata
* schema

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


import logging

logger = logging.getLogger("loader")


class CSVloader:
    r"""Loads a CSV, where the first line must contain the column (field) names
    and the following lines comma separated values.

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

    A list of column names::

        >>> csv.column_names
        ['a', 'b']

    More specific converters can be selected::
    TODO:: Add example with csv.get_device('device')(file)

    """

    def __init__(self, file, metadata=None, fields=None):
        self._file = file.read()
        self._metadata = metadata or {}
        self.fields = self.validate_fields(fields or self.create_fields())

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
        # import here to avoid cyclic dependencies
        # TODO: Implement the following converters
        # TODO: from .thiolab_labview_converter import ThiolabLabviewConverter
        # TODO: from .genericcsvconverter import GenericCsvConverter
        # TODO: from .eclabconverter import EclabConverter
        # TODO: Possibly allow extracting the device from the matadata file, i.e.,
        # device = None or metadata['instrument']['device']
        # But maybe this should rather be implemented in the CLI.
        from .eclabloader import ECLabLoader

        devices = {  #'generic' : GenericCsvLoader, # Generic CSV converter
            "eclab": ECLabLoader,  # Biologic-EClab device
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
        The header of the CVS (column names excluded).

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
    def column_names(self):
        r"""List of column (field) names describing the tabulated data.

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

    def schema(self):
        r"""
        A frictionless `Schema` object, including a `Fields` object
        describing the columns.
        The fields can be provided as argument to the loader or are
        constructed from the `column_names`.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.schema()
            {'fields': [{'name': 't'}, {'name': 'E'}, {'name': 'j'}]}

        from metadata::

            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
            >>> csv = CSVloader(file=file, metadata=metadata, fields=metadata['figure description']['schema']['fields'])
            >>> csv.schema()
            {'fields': [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema

        schema = Schema(fields=self.fields)

        return Schema(self._validated_schema(schema))

    def create_fields(self):
        r"""
        Creates a list of fields from the column names.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.create_fields()
            [{'name': 't'}, {'name': 'E'}, {'name': 'j'}]

        """
        return [{"name": name} for name in self.column_names]

    def _validated_schema(self, schema):
        r"""
        Returns an unchanged frictionless schema when the fields provided in the metadata or as argument
        in the schema are consistent with the column names in the CSV.

        EXAMPLES:

        A valid schema::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
            >>> schema = {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}
            >>> csv = CSVloader(file, metadata)
            >>> csv._validated_schema(schema)
            {'fields': [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema
        schema = Schema(schema)

        if not len(self.column_names) == len(schema.field_names):
            raise Exception(
                f"The number of columns ({len(self.column_names)}) does not match the number of fields ({len(schema.field_names)}) in the schema."
            )

        for name in self.column_names:
            if not name in schema.field_names:
                raise KeyError(
                    f"The schema does not have a description for the column with name '{name}'."
                )

        return schema

    def validate_fields(self, fields):
        r"""
        Returns an unchanged frictionless schema when the fields provided in the metadata or as argument
        in the schema are consistent with the column names in the CSV.

        EXAMPLES:

        A valid schema::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.validate_fields({})
            Traceback (most recent call last):
            ...
            Exception: The number of columns (3) does not match the number of fields (0).

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> fields = [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]
            >>> csv = CSVloader(file)
            >>> csv.validate_fields(fields)
            [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]

        """
        from frictionless import Schema
        schema = Schema(fields=fields)

        if not len(self.column_names) == len(schema.field_names):
            raise Exception(
                f"The number of columns ({len(self.column_names)}) does not match the number of fields ({len(schema.field_names)})."
            )

        for name in self.column_names:
            if not name in schema.field_names:
                raise KeyError(
                    f"^No field describes the column with name '{name}'."
                )

        return fields
