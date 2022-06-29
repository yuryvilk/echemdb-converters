

class ECConverter:
    """
    Creates standardized electrochemistry dataframes.

    The file loaded must have the columns t,U/E, and I/j.

    EXAMPLES::

        >>> from io import StringIO
        >>> file = StringIO(r'''t,E,j
        ... 0,0,0
        ... 1,1,1''')
        >>> from csvloader import CSVloader
        >>> metadata = {'figure description': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}
        >>> ec = ECConverter(CSVloader(file, metadata))
        >>> ec.df
           t  E  j
        0  0  0  0
        1  1  1  1

    A list of names describing the columns::

        >>> ec.column_names
        ['t', 'E', 'j']

        >>> ec.schema['fields']
        [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]

        >>> ec.schema.field_names
        ['t', 'E', 'j']

    """

    def __init__(self, loader):
        self.loader = loader

    def get_converter():
        pass

    @property
    def schema(self):
        from frictionless import Schema

        if not self.loader.metadata['figure description']['fields']:
            raise Exception('The `figure description` in the loaders metadata does not contain a field key.')

        schema = Schema(fields=self.loader.metadata['figure description']['fields'])

        for name in self.column_names:
            if not name in schema.field_names:
                raise KeyError(
                    f"Field with name {name} is not specified in `metadata.figure_description.fields`.")

        return schema

    @property
    def column_names(self):
        return self.loader.column_names

    @property
    def df(self):
        return self.loader.df
