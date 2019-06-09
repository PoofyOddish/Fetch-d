#Import necessary packages
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import requests
#import configparser
import json
import os

import random

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# API credentials
api_key = os.environ['PETFINDER_KEY']
api_secret = os.environ['PETFINDER_SECRET']
oath = requests.post('https://api.petfinder.com/v2/oauth2/token/',data=[('grant_type','client_credentials'),
                                                                 ('client_id',api_key),
                                                                ('client_secret',api_secret)])
zipcode = 80123
BASE = f'https://api.petfinder.com/v2/'
get_organizations = requests.get(BASE+f"organizations?location={zipcode}&distance=10&limit=100",headers={"Authorization":"Bearer "+oath.json()['access_token']})
organizations = {}

for org in get_organizations.json()['organizations']:
    organizations[org['name']]=org['id']
    #print(org)

org_list = ",".join(list(organizations.values()))

#print("Meet "+get_animals.json()['animals'][animal_num]['name']+"!")
#Image(url=get_animals.json()['animals'][animal_num]['photos'][0]['medium'])


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

#######

app.layout = html.Div([

    html.H1(children="Local Petfinder Analysis"),

    html.Div(children="I'm helping!"),

    html.Div([
        dcc.Dropdown(
            id='animal-type-selection',
            options=[{'label':i,'value':i} for i in ["Dog","Cat"]],
            value="Dog"
        ),
        
        dcc.Dropdown(
            id='animal-gender-selection',
            options=[{'label':i,'value':i} for i in ["Male","Female","No preference"]],
            value="No preference"
        ),
    ]),

    html.Div([
        html.Div(#dcc.Input(id='input-box', type='text')),
        html.Button('Next Pet', id='button'),)
        #html.Div(id='container-button-basic',
                #children='Enter a value and press submit')
    ]),

    html.Div([
        html.Img(
            id="pet-picture"
        )
    ]),

    #html.Div(id='pet-query', style={'display': 'none'})
    dcc.Store(id='pet-query'),

    html.Div([
        html.Div(id='pet-text')
    ])
])

@app.callback(
    Output('pet-query', 'data'),
    [Input('animal-type-selection', 'value'), 
    Input('animal-gender-selection', 'value')])
def update_query(animal_type, gender_value):
    query = {}
    query_string = ""
    #Questions

    #What type of animal are you looking for?
    query['type'] = animal_type.lower()
    query['gender'] = gender_value.lower()

    for key,values in query.items():
        if values != "" and values != "no preference":
            query_string = query_string+key+"="+values+"&"

    print(query_string)

    get_animals = requests.get(BASE+f"animals?organization={org_list}&{query_string}limit=50",headers={"Authorization":"Bearer "+oath.json()['access_token']})

    cleaned_animals = []

    for each in get_animals.json()['animals']:
        if len(each['photos']) != 0:
            cleaned_animals.append(each)

    return(json.dumps(cleaned_animals))

@app.callback(
    Output('button', 'n_clicks'),
    [Input('animal-type-selection', 'value'), 
    Input('animal-gender-selection', 'value')])
def reset(animal_type, gender_value):
    return(0)

@app.callback(
    Output('pet-picture', 'src'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_picture(query,clicks):

    loaded = json.loads(query)

    if clicks == None:
        clicks = 0

    query_length = len(loaded)-1
    looped = clicks // query_length

    number = clicks - looped * query_length

    print(clicks,query_length,looped,number)

    if query_length < 0 or query_length == None:
        src="https://cdn.shopify.com/s/files/1/2203/9263/products/96e0977de16d61248b634d1fa937bd8d.jpg?v=1538610080"
    else:
        src=loaded[number]['photos'][0]['medium']
    return(src)

@app.callback(
    Output('pet-text', 'children'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_text(query,clicks):

    loaded = json.loads(query)

    if clicks == None:
        clicks = 0

    query_length = len(loaded)-1
    looped = clicks // query_length

    number = clicks - looped * query_length


    if query_length < 0 or query_length == None:
        return("No results :(")
    else:
        return("Hey look, it's ",loaded[number]['name'].title(),"!")


if __name__ == '__main__':
    app.run_server(debug=True,port=5555)