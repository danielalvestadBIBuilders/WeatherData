import sys, os
from typing import List
import numpy as np
from global_variables import Respons, Item, Range,\
                             Coordinate, Element

import requests # See http://docs.python-requests.org/


def codec_utf8(s):
    '''Encode to utf-8'''
    return s.encode('utf-8').decode('utf-8') 

class Source:

    def __init__(self, id: str, name: str, location: Coordinate, county: str, country: str):
        self.id = id
        self.name = name
        self.location = location
        self.county = county
        self.country = country
        self.elements: List[Element] = []
    
    @classmethod
    def from_response_item(cls, item: Item):
        id = item['id']
        name = codec_utf8(item['name'])                               if 'name' in item else None
        location = Coordinate(long=item['geometry']['coordinates'][0], 
                              lat=item['geometry']['coordinates'][1]) if 'geometry' in item else None
        county = codec_utf8(item['county'])                           if 'county' in item else None
        country = codec_utf8(item['country'])                         if 'country' in item else None

        return cls(id,name,location,county,country)
    
    def get_time_series_info(self, client_id, elements) -> bool:
        r: Respons = self.request_timeseries_info(client_id, self.id, elements)

        # extract some data from the response
        if r.status_code == 200:
            for item in r.json()['data']:
                element_id = codec_utf8(item['elementId'])                if ('elementId' in item) else None
                valid_from = np.datetime64(codec_utf8(item['validFrom'])) if ('validFrom' in item) else None
                valid_to = np.datetime64(codec_utf8(item['validTo']))     if ('validTo' in item)   else np.datetime64('now')
                offset = codec_utf8(item['timeOffset'])                   if ('timeOffset' in item) else None
                resolution = codec_utf8(item['timeResolution'])           if ('timeResolution' in item) else None
                unit = codec_utf8(item['unit'])                           if ('unit' in item) else None
                hight_above_ground = item['level']['value']               if ('level' in item and 'value' in item['level']) else None
            
                self.elements.append(Element(element_id, valid_from, valid_to, offset, resolution, unit, hight_above_ground))
            
            return True
        else:
            api_error(r)
            return False

    
    def convert_resolution_to_numbers(self):
        
        resolutions = []
        for element in self.elements:
            try:
                resolution = element.resolution.replace('T','').split('P')[1][0:-1]
                unit = element.resolution.replace('T','').split('P')[1][-1]
                if unit=='H':   resolution = float(resolution) 
                elif unit=='M': resolution = float(resolution)/60.
                elif unit=='D': resolution = float(resolution)*24.
                else: raise Exception()
                resolutions.append(resolution)

            except:
                print("Some error in converting resolution for source: " + self.name)

        self.elements = list(map(lambda elem, res: Element(elem.element_id, 
                                                           elem.valid_from, 
                                                           elem.valid_to,
                                                           elem.offset, res,
                                                           elem.unit,
                                                           elem.hight_above_ground),
                                self.elements, resolutions)
                            )


    def request_timeseries_info(self, client_id: str, source_id: str, elements: List[str]) -> Respons:
        '''Send a get request for the available time series from <source_id>, 
        returns the respons which is a dictinoary'''
        # issue an HTTP GET request
        return requests.get('https://frost.met.no/observations/availableTimeSeries/v0.jsonld',
                           {'sources': source_id, 'elements': ','.join(elements)},
                            auth=(client_id, '')
    )


def request_source_info(client_id: str, source_ids: str = None, county: str = None) -> Respons:
    '''Send a get request for info about <source_id>, 
    returns the respons which is a dictinoary'''
    params = dict()
    
    if source_ids:
        params['ids'] = source_ids
    if county:
        params['county'] = county
    
    # issue an HTTP GET request
    return requests.get(
        'https://frost.met.no/sources/v0.jsonld',
        params,
        auth=(client_id, '')
    )
    
        

def create_sources(client_id, elements, source_ids: str = None, county: str = None) -> Source:
    r: Respons = request_source_info(client_id, source_ids = source_ids, county=county)
    # Create source objects
    if r.status_code == 200:
        sources: List[Source] = []
        for item in r.json()['data']:
            source = Source.from_response_item(item)
            if source.get_time_series_info(client_id, elements):
                sources.append(source)
                print(source.name)
        
        return sources
    else:
        api_error(r)

def api_error(r):
    sys.stdout.write('error:\n')
    sys.stdout.write('\tstatus code: {}\n'.format(r.status_code))
    if 'error' in r.json():
        assert(r.json()['error']['code'] == r.status_code)
        sys.stdout.write('\tmessage: {}\n'.format(r.json()['error']['message']))
        sys.stdout.write('\treason: {}\n'.format(r.json()['error']['reason']))
    else:
        sys.stdout.write('\tother error\n')
