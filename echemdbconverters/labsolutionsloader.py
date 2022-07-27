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

from csvloader import CSVloader

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
    }

class LabSolutionsLoader(CSVloader):

    @property
    def header_lines(self):
        pass

    @property
    def df(self):
        # import pandas as pd

        # return pd.read_csv(
        #     self.file,
        #     sep=self.delimiter,
        #     header=self.header_lines,
        #     decimal=self.decimal,
        #     encoding="latin1",
        #     skip_blank_lines=False,
        # )
        pass

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
    def decimal(self):
        # The values in the MPT are always tab separated.
        # The data in the file only consist of numbers.
        # Hence we simply determine if the line contains a comma or not.
        if "," in self.data.readlines()[0]:
            return ","

        return "."

    def blocks(self):
        matches = {}
        # empty_lines = []
        for ln, line in enumerate(self.file.readlines()):
            import re

            match = re.match(
                '\[(.*?)\]', line, re.IGNORECASE,
            )

            if match:
                matches[match] = [ln]
                for ln, line in enumerate(self.file.readlines()[ln:]):
                    if len(line.split()) < 1:
                        matches[match].append(ln)
                        break
            # if len(line.split()) < 1:
            #     empty_lines.append(ln)
        print(matches)
        # self.file


from pathlib import Path    
doc = Path("D:\Research Data\Yury Vilk\OwnCloud\PhD\Analytics\HPLC\RawData\Luis\\20220715\LK005_df10_240min.txt")
f = LabSolutionsLoader(doc.open())
f.blocks()