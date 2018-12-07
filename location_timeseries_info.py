
import numpy as np
import pandas as pd
import requests # See http://docs.python-requests.org/

#Plotting
import seaborn as sns
#import plotly.plotly as py
import plotly.figure_factory as ff
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
init_notebook_mode()


from typing import List, Dict

from Source import Source, create_sources
from global_variables import Respons, Item, Range, Coordinate, Element


from collections import namedtuple
Coordinate = namedtuple('Coordinate', ['long', 'lat'])
Element = namedtuple('Element', ['element_id', 'valid_from', 'valid_to', 'offset', 'resolution', 'unit', 'hight_above_ground'])



# REMOVE THIS IF PUBLISH CODE!!!
#
CLIENT_ID = "846c06a4-47be-44ec-a1f9-b1a3142b1e8f"
#
#

SOURCE_IDS = 'SN44620,SN44610,SN76920,SN44560'

ELEMENTS = ['air_temperature', 
            'wind_speed',
            'wind_from_direction',
            'air_pressure_at_sea_level',
            'cloud_area_fraction',
            'boolean_clear_sky_weather(cloud_area_fraction P1D)',
            'sum(precipitation_amount PT1H)']

# Master range
DATE_RANGE = [np.datetime64('1950-01-01'),np.datetime64('now')]

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

def create_intervals_for_source_id(element_ids: str, source: Source) -> List[Dict]:
    intervals = []
    for element_id in element_ids:
        source_elements = [element for element in source.elements if (element.element_id == element_id)]
        start = [element.valid_from for element in source_elements]
        stop = [element.valid_to for element in source_elements]

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
        
        max_resolution_in_range = create_interval_resolution_array(ranges, source_elements)
        
        ranges, resolutions = merge_similar_resolution_neighbors(ranges, max_resolution_in_range)

        for rng, res in zip(ranges, resolutions):
            intervals.append(dict(Task=element_id, Start=rng[0], Finish=rng[1], Resource=res))
    return intervals

def create_intervals_for_element_id(element_id: str, sources: List[Source]) -> List[Dict]:
    intervals = []
    for source in sources:
        elements = [element for element in source.elements if (element.element_id == element_id)]
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
    return intervals
            

sources = create_sources(CLIENT_ID, elements=ELEMENTS, county='Møre og Romsdal') #source_ids = SOURCE_IDS)
for source in sources:
    source.convert_resolution_to_numbers()

from plotly.graph_objs import Scattermapbox,Data,Layout

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import json
from textwrap import dedent as d
#import pandas as pd
#import plotly.graph_objs as go

mapbox_access_token = 'pk.eyJ1IjoiYWx2ZXN0YWQxMCIsImEiOiJjanBjZDBwZmkweW1uM3BwMm93emg3dnA4In0.0bVLzQoLNShuPPP4SK9umA'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#app = JupyterDash('SimpleExample')

app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id = 'Map',
            figure = {
        'data': [Scattermapbox(
                    lat= [source.location[1] for source in sources if source.location != None],
                    lon= [source.location[0] for source in sources if source.location != None],
                    #color = df['MAPE_scaled'],
                    text = [source.name for source in sources if source.location != None],
                    mode='markers',
                    marker = dict(color = 'rgb(0, 128, 0)',size=10)
                ) ] ,
        'layout': dict(
                    title = "Source locations",
                    #font=dict(family='Courier New, monospace', size=18, color='rgb(0,0,0)'),
                    autosize=False,
                    hovermode='closest',
                    showlegend=False,
                    #width=1000,
                    #height=1000,
                    mapbox=dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        center=dict(
                            lat=61.57087829981879,
                            lon=14.439860118363981
                        ),
                        pitch=0,
                        zoom=3.084654241259188,
                        style = 'light'
                    ),
                )        
            }
        )
    ]),
    html.Div([
        dcc.Graph(id='Available-range'),
    ]),
])

def create_time_series(intervals, title):
    fig = ff.create_gantt(intervals, index_col='Resource', show_colorbar=True, group_tasks=True)
    return fig

@app.callback(
    dash.dependencies.Output('Available-range', 'figure'),
    [dash.dependencies.Input('Map', 'hoverData')])
def update_y_timeseries(hoverData):
    global sources
    if hoverData != None:
        source_name = hoverData['points'][0]['text']
        source = [source for source in sources if source.name == source_name][0]
    else:
        source = sources[0]
    intervals = create_intervals_for_source_id(ELEMENTS, source)
    return ff.create_gantt(intervals, index_col='Resource', show_colorbar=True, group_tasks=True)

    #return create_time_series(intervals_all_elements, title)

app.run_server(debug=True)






"""

#from jupyter_plotly_dash import JupyterDash

import dash
import dash_core_components as dcc
import dash_html_components as html
#import pandas as pd
#import plotly.graph_objs as go

mapbox_access_token = 'pk.eyJ1IjoiYWx2ZXN0YWQxMCIsImEiOiJjanBjZDBwZmkweW1uM3BwMm93emg3dnA4In0.0bVLzQoLNShuPPP4SK9umA'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#app = JupyterDash('SimpleExample')

app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='Location-Map',
            hoverData={'source': [{'name': 'SOLA'}]}
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(id='Available-range'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Div(dcc.Slider(
        id='crossfilter-year--slider',
        min=DATE_RANGE[0],
        max=DATE_RANGE[1],
        value=DATE_RANGE[0],
    ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
])


@app.callback(
    dash.dependencies.Output('Location-Map', 'figure'),
    [dash.dependencies.Input('crossfilter-year--slider', 'value')])
def update_graph(year_value):
    global sources
    return {
        'data': [Scattermapbox(
                    lat= [source.location[1] for source in sources if source.location != None],
                    lon= [source.location[0] for source in sources if source.location != None],
                    #color = df['MAPE_scaled'],
                    text = [source.name for source in sources if source.location != None],
                    mode='markers',
                    marker = dict(color = 'rgb(0, 128, 0)',size=10)
                ) ] ,
        'layout': dict(
                    title = "Source locations",
                    #font=dict(family='Courier New, monospace', size=18, color='rgb(0,0,0)'),
                    autosize=False,
                    hovermode='closest',
                    showlegend=False,
                    #width=1000,
                    #height=1000,
                    mapbox=dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        center=dict(
                            lat=61.57087829981879,
                            lon=14.439860118363981
                        ),
                        pitch=0,
                        zoom=3.084654241259188,
                        style = 'light'
                    ),
                )        
            }


def create_time_series(intervals, title):
    fig = ff.create_gantt(intervals, index_col='Resource', show_colorbar=True, group_tasks=True)
    return fig


@app.callback(
    dash.dependencies.Output('Available-range', 'figure'),
    [dash.dependencies.Input('Location-Map', 'hoverData')])
def update_y_timeseries(hoverData):
    global sources
    source_name = hoverData['source'][0]['name']
    sources = [source for source in sources if source.name == source_name]
    intervals_all_elements = []
    for element_id in ELEMENTS:
        intervals_all_elements.append(create_intervals_for_element_id(element_id, sources)[0])
    title = 'Available ranges for; <b>{}</b>'.format(source_name)
    return create_time_series(intervals_all_elements, title)

app.run_server(debug=True)

"""