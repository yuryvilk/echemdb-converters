r"""
Loader for CSV files (https://datatracker.ietf.org/doc/html/rfc4180)
which consist of a single header line containing the column (field)
names and rows with comma separated values.

In pandas the names of the columns are referred to as `column_names`,
whereas in a frictionless datapackage the column names are called `fields`.
The latter is a descriptor containing, including information about, i.e.,
the type of data, a title or a description.

The CSV object has the following properties:
::TODO: Add examples for the following functions
    * a DataFrame
    * the column names
    * the header contents
    * the number of header lines
    * metadata
    * schema

Loaders for non standard CSV files can be called:

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
    r"""
    Loads a CSV, where the first line must contain the column (field) names
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
        self._fields = fields

    @property
    def file(self):
        r"""
        A file like object of the loaded CSV.

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

    @property
    def fields(self):
        r"""
        Fields describing the column names.

        EXAMPLES:

        If not specified, the fields are created from the `column_names`.::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.fields
            [{'name': 't', 'comment': 'Created by echemdb-converters.'}, {'name': 'E', 'comment': 'Created by echemdb-converters.'}, {'name': 'j', 'comment': 'Created by echemdb-converters.'}]

        The fields can be provided as an argument to the loader.::

            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
            >>> csv = CSVloader(file=file, metadata=metadata, fields=metadata['figure description']['schema']['fields'])
            >>> csv.fields
            [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]

        When a field is missing (here `t`) it will be generated and all obsolete fields descriptions (here `x`) are removed.::

            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'},{'name': 'x'}]}}}
            >>> csv = CSVloader(file=file, metadata=metadata, fields=metadata['figure description']['schema']['fields'])
            >>> csv.fields
            [{'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}, {'name': 't', 'comment': 'Created by echemdb-converters.'}]

        """
        #_fields = self._fields
        if not self._fields:
            return self.create_fields()

        from frictionless import Schema, Field

        # Validate if fields are valid frictionless fields.
        schema = Schema(fields=[Field(field) for field in self._fields])

        # Validate that the fields have an attribute 'name'
        # and remove the field if not available.
        for field in schema.fields:
            try:
                field['name']
            except KeyError:
                schema.fields.remove(field)
                logger.warning("Field {field} has no attribute `name`.")

        # Remove fields which are not found in the column names.
        for name in schema.field_names:
            if not name in self.column_names:
                schema.remove_field(name)

        # Add fields for columns names that are not described in the provided fields.
        for name in self.column_names:
            if not name in schema.field_names:
                schema.add_field(self.create_field(name))
                logger.warning("A field with name `{name}` was added to the schema.")

        return schema.fields

    @property
    def metadata(self):
        r"""
        Metadata constructed from input metadata and the CSV header.
        A simple CSV does not have any metadata in the header.

        EXAMPLES::

        Without metadata::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.metadata
            {}

        Without metadata provided to the loader::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file, metadata={'foo':'bar'})
            >>> csv.metadata
            {'foo': 'bar'}

        """
        return self._metadata.copy()

    @staticmethod
    def get_loader(device=None):
        r"""
        Calls a specific `loader` based on a given device.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO('''EC-Lab ASCII FILE
            ... Nb header lines : 6
            ...
            ... Device metadata : some metadata
            ...
            ... mode\ttime/s\tEwe/V\t<I>/mA\tcontrol/V
            ... 2\t0\t0.1\t0\t0
            ... 2\t1\t1.4\t5\t1
            ... ''')
            >>> csv = CSVloader.get_loader('eclab')(file)
            >>> csv.df
            mode  time/s Ewe/V  <I>/mA  control/V
            0     2       0   0.1       0          0
            1     2       1   1.4       5          1

        """
        from .eclabloader import ECLabLoader
        from .labsolutionsloader import LabSolutionsLoader

        devices = {
            "eclab": ECLabLoader,    # Biologic-EClab device
            'hplc': LabSolutionsLoader,    # Shimadzu HPLC device
            'gc': LabSolutionsLoader    # Shimadzu GC device
        }

        if device in devices:
            return devices[device]

        raise KeyError(f"Device wth name '{device}' is unknown to the loader'.")

    @property
    def df(self):
        r"""
        A pandas dataframe of the data in the CSV.

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
    def data(self):
        r"""
        A file like object with the data of the CSV without header lines.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> type(csv.data)
            <class '_io.StringIO'>

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.data.readlines()
            ['0,0\n', '1,1']

        """
        from io import StringIO

        return StringIO(
            "".join(line for line in self.file.readlines()[self.header_lines + 1 :])
        )

    @property
    def column_names(self):
        r"""
        List of column (field) names describing the tabulated data.

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
        The number of header lines in a CSV excluding the line with the column names.

        EXAMPLES:

        Files for the base loader do not have a header::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.header_lines
            0

        Implementation in a specific device loader::

            >>> file = StringIO('''EC-Lab ASCII FILE
            ... Nb header lines : 6
            ...
            ... Device metadata : some metadata
            ...
            ... mode\ttime/s\tEwe/V\t<I>/mA\tcontrol/V
            ... 2\t0\t0,1\t0\t0
            ... 2\t1\t1,4\t5\t1
            ... ''')
            >>> csv = CSVloader.get_loader('eclab')(file)
            >>> csv.header_lines
            5

        """
        return 0

    @property
    def schema(self):
        r"""
        A frictionless `Schema` object, including a `Fields` object
        describing the columns.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> from .csvloader import CSVloader
            >>> csv = CSVloader(file)
            >>> csv.schema
            {'fields': [{'name': 't', 'comment': 'Created by echemdb-converters.'}, {'name': 'E', 'comment': 'Created by echemdb-converters.'}, {'name': 'j', 'comment': 'Created by echemdb-converters.'}]}

        Field description provided in the metadata::

            >>> file = StringIO(r'''t,E,j
            ... 0,0,0
            ... 1,1,1''')
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
            >>> csv = CSVloader(file=file, metadata=metadata, fields=metadata['figure description']['schema']['fields'])
            >>> csv.schema
            {'fields': [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema

        return Schema(fields=self.fields)

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
            [{'name': 't', 'comment': 'Created by echemdb-converters.'}, {'name': 'E', 'comment': 'Created by echemdb-converters.'}, {'name': 'j', 'comment': 'Created by echemdb-converters.'}]

        """
        return [self.create_field(name) for name in self.column_names]

    @classmethod
    def create_field(cls, name):
        r"""
        Creates a field with a specified name.

        EXAMPLES::

            >>> CSVloader.create_field('voltage')
            {'name': 'voltage', 'comment': 'Created by echemdb-converters.'}

        """
        return {"name": name, 'comment': 'Created by echemdb-converters.'}

    @property
    def delimiter(self):
        r"""
        The delimiter in the CSV, which is extracted from
        the first two lines of the CSV data.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.delimiter
            ','

        """
        import clevercsv

        # Only two lines are used to detect the delimiter,
        # since clevercsv is slow with files containing many columns.
        return clevercsv.detect.Detector().detect(self.data.read()[:2]).delimiter

    @property
    def decimal(self):
        r"""
        The decimal separator in the floats in the CSV data.

        EXAMPLES:

        Not implemented in the base loader::

            >>> from io import StringIO
            >>> file = StringIO(r'''a,b
            ... 0,0
            ... 1,1''')
            >>> csv = CSVloader(file)
            >>> csv.decimal
            Traceback (most recent call last):
            ...
            NotImplementedError

        Implementation in a specific device loader::

            >>> file = StringIO('''EC-Lab ASCII FILE
            ... Nb header lines : 6
            ...
            ... Device metadata : some metadata
            ...
            ... mode\ttime/s\tEwe/V\t<I>/mA\tcontrol/V
            ... 2\t0\t0,1\t0\t0
            ... 2\t1\t1,4\t5\t1
            ... ''')
            >>> csv = CSVloader.get_loader('eclab')(file)
            >>> csv.decimal
            ','

        """
        raise NotImplementedError
