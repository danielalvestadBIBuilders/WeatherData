import numpy as np

# Define Types
from typing import List, Dict

Respons = List[str]
Item = Dict[str,str]
Range = List[np.datetime64]


# Define named tuples
from collections import namedtuple
Coordinate = namedtuple('Coordinate', ['long', 'lat'])
Element = namedtuple('Element', ['element_id', 'valid_from', 'valid_to', 'offset', 'resolution', 'unit', 'hight_above_ground'])



