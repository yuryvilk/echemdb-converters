from .converter import ECConverter


class ECLabConverter(ECConverter):
    r"""
    Some description.

    EXAMPLES::

        >>> from io import StringIO
        >>> file = StringIO('''EC-Lab ASCII FILE
        ... Nb header lines : 6
        ...
        ... Device metadata : some metadata
        ...
        ... mode\ttime/s\tEwe/V\t<I>/mA\tcontrol/V
        ... 2\t0\t0\t0\t0
        ... 2\t1\t1.4\t5\t1
        ... ''')
        >>> from .csvloader import CSVloader
        >>> ec = ECLabConverter(CSVloader.get_loader('eclab')(file))
        >>> ec.df
           t  E  I
        0  0  0  0
        1  1  5  1

    """

    @property
    def name_conversion(self):

        return {
            "time/s": "t",
            "Ewe/V": "E",
            "<I>/mA": "I",
        }
