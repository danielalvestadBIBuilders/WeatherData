import numpy as np
import pandas as pd
import requests # See http://docs.python-requests.org/

#Plotting
import seaborn as sns
import plotly.plotly as py
import plotly.figure_factory as ff

from typing import List, Dict

from Source import Source, create_sources
from global_variables import Respons, Item, Range,\
                             Coordinate, Element

    
def overlap_interval(range1, range2):
    return (range2[0] <= range1[0] < range2[1]) or (range2[0] < range1[1] <= range2[1])



def create_interval_resolution_array(ranges: List[Range], elements: List[Element]) -> List[str]:
    
    max_resolution_in_range = []
    
    for range in ranges:
        resolutions_in_range = []
        for element in elements:
            valid_from_to_range = [element.valid_from,element.valid_to]
            if overlap_interval(range, valid_from_to_range):
                resolutions_in_range.append(element.resolution)
                   
            
        if len(resolutions_in_range) > 0:
            rs = min(resolutions_in_range)
            if rs < 1.0:
                max_resolution_in_range.append('1H>')
            elif rs == 1.0:
                max_resolution_in_range.append('1H')
            elif rs > 1.0 and rs < 24.0:
                max_resolution_in_range.append('1H<')
            elif rs == 24.0:
                max_resolution_in_range.append('1D')
            elif rs > 24.0:
                max_resolution_in_range.append('1D<')

        else:
            max_resolution_in_range.append('No Data')
    return max_resolution_in_range


def merge_similar_resolution_neighbors(ranges: List[Range], resolutions: List[str]) -> (List[Range], List[str]):
    
    tmp_ranges = [ranges[0]]
    tmp_resolutions = [resolutions[0]]

    for res, rng in zip(resolutions[1:], ranges[1:]):
        # Check if the next range have same reolution
        if res != tmp_resolutions[-1]:
            tmp_resolutions.append(res)
            tmp_ranges.append(rng)
        else:
            tmp_ranges[-1] = [tmp_ranges[-1][0], rng[1]]

    return tmp_ranges, tmp_resolutions



if __name__ == "__main__":

    # Define some global variables
    
    # REMOVE THIS IF PUBLISH CODE!!!
    #
    CLIENT_ID = "846c06a4-47be-44ec-a1f9-b1a3142b1e8f"
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


    
    sources = create_sources(CLIENT_ID, elements=ELEMENTS, source_ids=SOURCE_IDS)

    intervals = []
    for source in sources:
        source.convert_resolution_to_numbers()

        elements = [element for element in source.elements if (element.element_id == ID)]
        start = [element.valid_from for element in elements]
        stop = [element.valid_to for element in elements]

        ranges = []

        #----- create ranges ------
        sort_dates = np.array(start + stop)
        sort_dates = sort_dates[np.argsort(sort_dates)]

        if len(sort_dates) == 0:
            ranges.append(DATE_RANGE)
        else:
            ranges.append([DATE_RANGE[0],sort_dates[0]])
            for i,date in enumerate(sort_dates[1:], start=1): ranges.append([sort_dates[i-1],date])
            ranges.append([sort_dates[-1],DATE_RANGE[1]])

        #----- Find overapping ranges -----
        
        max_resolution_in_range = create_interval_resolution_array(ranges, elements)

        ranges, resolutions = merge_similar_resolution_neighbors(ranges, max_resolution_in_range)

        for rng, res in zip(ranges, resolutions):
            intervals.append(dict(Task=source.name, Start=rng[0], Finish=rng[1], Resource=res))


    #groups = ['No Data', '1D<', '1D', '1H<', '1H', '1H>']
    #colors = {'Not Started': 'rgb(220, 0, 0)',
    #          'Incomplete': (1, 0.9, 0.16),
    #          'Complete': 'rgb(0, 255, 100)'}

    fig = ff.create_gantt(intervals, index_col='Resource', show_colorbar=True, group_tasks=True)
    py.iplot(fig, filename='gantt-group-tasks-together', world_readable=True)







    """
    source_ranges = dict()
    # Create range of availability for each element
    for source in sources:
        availability_ranges = dict()
        for element_id in ELEMENTS:

            elements = [element for element in source.elements if (element.element_id == element_id)]
            if len(elements) > 0:
                min_date = min([element.valid_from for element in elements])
                current = np.datetime64('now')
                max_date = max([(element.valid_to if element.valid_to != None else current) for element in elements])
                min_res = max([element.resolution for element in elements])

                availability_ranges[element_id] = [min_date, max_date, min_res]

        source_ranges[source.name] = availability_ranges

            
    print(pd.DataFrame.from_dict(source_ranges))
    """
    


#Example 2 - Get a time series
#!/usr/bin/python

"""
    # extract command-line argument
    if len(sys.argv) != 2:
       sys.stderr.write('usage: ' + sys.argv[0] + ' <source ID>\n')
       sys.exit(1)
    source_id = sys.argv[1]

    # extract environment variable
    if not 'CLIENTID' in os.environ:
        sys.stderr.write('error: CLIENTID not found in environment\n')
        sys.exit(1)
    client_id = os.environ['CLIENTID']

    # issue an HTTP GET request
    r = requests.get(
        'https://frost.met.no/sources/v0.jsonld',
        {'ids': source_id},
        auth=(client_id, '')
    )







This program shows how to retrieve a time series of observations from the following
combination of source, element and time range:

source:     SN18700
element:    mean(wind_speed P1D)
time range: 2010-04-01 .. 2010-05-31

The time series is written to standard output as lines of the form:

  <observation time as date/time in ISO 8601 format> \
  <observation time as seconds since 1970-01-01T00:00:00> \
  <observed value>

Save the program to a file example.py, make it executable (chmod 755 example.py),
and run it e.g. like this:

  $ CLIENTID=8e6378f7-b3-ae4fe-683f-0db1eb31b24ec ./example.py

(Note: the client ID used in the example should be replaced with a real one)

The program has been tested on the following platforms:
  - Python 2.7.3 on Ubuntu 12.04 Precise
  - Python 2.7.12 and 3.5.2 on Ubuntu 16.04 Xenial

"""
"""
import sys, os
import dateutil.parser as dp
import requests # See http://docs.python-requests.org/

if __name__ == "__main__":

    # extract client ID from environment variable
    if not 'CLIENTID' in os.environ:
        sys.stderr.write('error: CLIENTID not found in environment\n')
        sys.exit(1)
    client_id = os.environ['CLIENTID']

    # issue an HTTP GET request
    r = requests.get(
        'https://frost.met.no/observations/v0.jsonld',
        {'sources': 'SN18700', 'elements': 'mean(wind_speed P1D)', 'referencetime': '2010-04-01/2010-06-01'},
        auth=(client_id, '')
    )

    # extract the time series from the response
    if r.status_code == 200:
        for item in r.json()['data']:
            iso8601 = item['referenceTime']
            secsSince1970 = dp.parse(iso8601).strftime('%s')
            sys.stdout.write('{} {} {}\n'.format(iso8601, secsSince1970, item['observations'][0]['value']))
    else:
        sys.stdout.write('error:\n')
        sys.stdout.write('\tstatus code: {}\n'.format(r.status_code))
        if 'error' in r.json():
            assert(r.json()['error']['code'] == r.status_code)
            sys.stdout.write('\tmessage: {}\n'.format(r.json()['error']['message']))
            sys.stdout.write('\treason: {}\n'.format(r.json()['error']['reason']))
        else:
            sys.stdout.write('\tother error\n')
"""