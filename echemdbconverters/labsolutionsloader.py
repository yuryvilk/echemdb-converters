"""
Loads ASCII (.txt) files recorded with Shimadzu LabSolutions software
from Shimadzu HPLC or GC systems and converted to ASCII from PostRun or Batch.
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

from tkinter import E
from csvloader import CSVloader

"""
detectors = {
    'UV-ViS': {},
    'RID': {},
    'BID': {}
}


chromatograms = {
    'UV-ViS': { #UV-ViS Detector (HPLC)
        'block' : [],
        'block_length_line_idx_shift' : 2, 
        'block_start_line_shift' : 8
    },
    'RID': {    # Refractive index detector (HPLC)
        'block' : [],
        'block_length_line_idx_shift' : 2, 
        'block_start_line_shift' : 7
    },
    'BID': {
        'block': [],    # Barrier ionization detector (GC)
        'block_length_line_idx_shift' : 0,  #TODO: fill appropriate values
        'block_start_line_shift' : 0  #TODO: fill appropriate values
    }
    }
peaktables = {
    'UV-ViS': {
        'block' : [],
        'block_length_line_idx_shift' : 1, 
        'block_start_line_shift' : 2
    },
    'RID': {
        'block' : [],
        'block_length_line_idx_shift' : 1, 
        'block_start_line_shift' : 2
    },
    'BID': {
        'block': [],    # Barrier ionization detector (GC)
        'block_length_line_idx_shift' : 0,  #TODO: fill appropriate values
        'block_start_line_shift' : 0  #TODO: fill appropriate values
    }
    }
compoundtables = {
    'UV-ViS': {
        'block' : [],
        'block_length_line_idx_shift' : 1, 
        'block_start_line_shift' : 2
    },
    'RID': {
        'block' : [],
        'block_length_line_idx_shift' : 1, 
        'block_start_line_shift' : 2
    },
    'BID': {
        'block': [],    # Barrier ionization detector (GC)
        'block_length_line_idx_shift' : 0,  #TODO: fill appropriate values
        'block_start_line_shift' : 0  #TODO: fill appropriate values
    }
    }"""

class LabSolutionsLoader(CSVloader):

    @property
    def header_lines(self, block):
        return self.blocks[block][-2]

    @property
    def data(self, block):
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
            "".join(line for line in self.file.readlines()[self.header_lines : self.blocks[block][-1]])
        )

    @property
    def df(self):
        import pandas as pd

        return pd.read_csv(
            self.file,
            sep=self.delimiter,
            header=self.header_lines,
            decimal=self.decimal,
            encoding="latin1",
            skip_blank_lines=False,
        )

    def create_fields(self):
        # TODO:: When the file contains an unnamed column an this is not 13, this approach will fail. (see: #8)
        # return [
        #     field
        #     for field in biologic_fields
        #     for name in self.column_names
        #     if name == field["name"]
        # ]
        pass

    @property
    def decimal(self, block):
        # The values in the MPT are always tab separated.
        # The data in the file only consist of numbers.
        # Hence we simply determine if the line contains a comma or not.
        if "," in self.data.readlines()[0]:
            return ","
        else:
            return "."

    @property
    def blocks(self):
        self.matches = {} # 'block name' : [block line start, data header line, block end]
        for ln, line in enumerate(self.file.readlines()):
            import re

            match = re.match(
                '\[(.*?)\]', line, re.IGNORECASE,
            )

            if match:
                self.matches[match.group()] = [ln]
                for l, line in enumerate(self.file.readlines()[ln:]):
                    if len(line.split()) < 1:
                        self.matches[match.group()].append(ln+l)
                        break
        for values in self.matches.values():
            try:   
                for ln, line in enumerate(self.file.readlines()[values[0]:values[1]]):
                    info = re.match('# of', line)
                    if info:
                        info = info.string.rstrip().split('\t')
                        data_block_length = int(info[-1])
                        if data_block_length != 0:
                            data_header_line = values[1]- int(info[-1]) - 1
                            values.insert(1, data_header_line)
                        else:
                            pass
            except IndexError:
                pass
        return self.matches

from pathlib import Path    
doc = Path("D:\Research Data\Yury Vilk\OwnCloud\PhD\Analytics\HPLC\RawData\Luis\\20220715\LK005_df10_240min.txt")
f = LabSolutionsLoader(doc.open())
b = f.blocks
