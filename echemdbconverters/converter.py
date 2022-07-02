import logging
logger = logging.getLogger("converters")

class ECConverter:
    """
    Creates standardized echemdb datapackage compatible CSV.

    The file loaded must have the columns t, U/E, and I/j.

    EXAMPLES::

        >>> from io import StringIO
        >>> file = StringIO(r'''t,E,j
        ... 0,0,0
        ... 1,1,1''')
        >>> from .csvloader import CSVloader
        >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'}]}}}
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

    def get_converter(device=None):
        r"""
        Calls a specific `converter` based on a given device.
        """
        # import here to avoid cyclical dependencies
        # TODO: Implement the following converters
        # TODO: from .thiolab_labview_converter import ThiolabLabviewConverter
        # TODO: from .genericcsvconverter import GenericCsvConverter
        # TODO: from .eclabconverter import EclabConverter
        # The following dict is a placeholder for further specific converters.
        # They hare here to get an idea what this function should do. These are currently not tested.
        from .eclabconverter import ECLabConverter

        devices = {  #'generic' : GenericCsvLoader, # Generic CSV converter
            "eclab": ECLabConverter,  # Biologic-EClab device
            #'Thiolab Labview' : ThiolabLabviewLoader, # Labview data recorder formerly used in the thiolab
        }

        if device in devices:
            return devices[device]

        raise KeyError(f"Device wth name '{device}' is unknown to the converter'.")

    def name_conversion(self):
        return {}

    @classmethod
    def _validate_core_dimensions(cls, column_names):
        """
        Validates that the column names contain a time, voltage and current axis.

        EXAMPLES::

            >>> ECConverter._validate_core_dimensions(['t','U','I'])
            True

            >>> ECConverter._validate_core_dimensions(['t','U'])
            Traceback (most recent call last):
            ...
            KeyError: "No column with a 'current' axis."

        """
        core_dimensions = {'time': ['t'], 'voltage': ['E', 'U'], 'current': ['I', 'j']}

        for key in core_dimensions:
            if not set(core_dimensions[key]).intersection(set(column_names)):
                raise KeyError(f"No column with a '{key}' axis.")
        return True

    @classmethod
    def get_electrochemistry_dimensions(cls, column_names):
        """
        Creates standardized electrochemistry dataframes.

        The file loaded must have the columns t, U/E, and I/j,
        but may contain any other columns related to the EC data.

        EXAMPLES::

            >>> ECConverter.get_electrochemistry_dimensions(['t', 'y', 'U', 'E', 'x', 'j'])
            ['t', 'E', 'U', 'j']

        """
        cls._validate_core_dimensions(column_names)

        valid_dimensions = {'time': ['t'], 'voltage': ['E', 'U'], 'current': ['I', 'j']}

        available_dimensions = []

        for key, items in valid_dimensions.items():
            for item in items:
                if item in column_names:
                    available_dimensions.append(item)

        return available_dimensions

    @property
    def schema(self):
        """
        Creates an ec schema.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j,x
            ... 0,0,0,0
            ... 1,1,1,1''')
            >>> from .csvloader import CSVloader
            >>> metadata = {'figure description': {'schema': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'},{'name':'x', 'unit':'m'}]}}}
            >>> ec = ECConverter(CSVloader(file, metadata))
            >>> ec.schema
            {'fields': [{'name': 't', 'unit': 's'}, {'name': 'E', 'unit': 'V', 'reference': 'RHE'}, {'name': 'j', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema

        schema = Schema(fields=[self.loader.schema.get_field(dimension) for dimension in self.column_names])

        return schema

    @property
    def column_names(self):
        """
        The EC file must have three dimensions, including time, voltage and current.
        Possibly construct column names in here.
        """
        return self.get_electrochemistry_dimensions(self.loader.column_names)

    @property
    def df(self):
        """
        Creates standardized electrochemistry dataframes.

        The file loaded must have the columns t, U/E, and I/j,
        but may contain any other columns related to the EC data.

        EXAMPLES::

            >>> from io import StringIO
            >>> file = StringIO(r'''t,E,j,x
            ... 0,0,0,0
            ... 1,1,1,1''')
            >>> from .csvloader import CSVloader
            >>> metadata = {'figure description': {'fields': [{'name':'t', 'unit':'s'},{'name':'E', 'unit':'V', 'reference':'RHE'},{'name':'j', 'unit':'uA / cm2'},{'name':'x', 'unit':'m'}]}}
            >>> ec = ECConverter(CSVloader(file, metadata))
            >>> ec.get_electrochemistry_dimensions(ec.loader.column_names)
            ['t', 'E', 'j']

        """
        return self.loader.df[self.get_electrochemistry_dimensions(self.column_names)]
