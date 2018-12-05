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



# REMOVE THIS IF PUBLISH CODE!!!
#
CLIENTID = "846c06a4-47be-44ec-a1f9-b1a3142b1e8f"
#
#

SOURCE_IDS = 'SN76931,SN76927,SN76926,SN76923,SN76933,SN76930,SN76928,SN76900,SN44640,SN44620,SN44610,SN76920,SN76922,SN76925,SN76956,SN44560,SN44580'

ELEMENTS = ['air_temperature', 
            'wind_speed',
            'wind_from_direction',
            'air_pressure_at_sea_level',
            'cloud_area_fraction',
            'boolean_clear_sky_weather(cloud_area_fraction P1D)',
            'sum(precipitation_amount PT1H)']

# Master range
DATE_RANGE = [np.datetime64('1950-01-01'),np.datetime64('now')]

ID = 'boolean_clear_sky_weather(cloud_area_fraction P1D)'
