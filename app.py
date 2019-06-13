# Petfinder - Fetch'd Application Code
# Features to add:
# Zipcode input


#Import necessary packages
import requests
import json
import os
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State

# API credentials
# API key and secret saved in Heroku
api_key = os.environ['PETFINDER_KEY']
api_secret = os.environ['PETFINDER_SECRET']

query_results = pd.DataFrame().to_dict('records')

# OATH for Petfinder session
oath = requests.post('https://api.petfinder.com/v2/oauth2/token/',data=[('grant_type','client_credentials'),
                                                                 ('client_id',api_key),
                                                                ('client_secret',api_secret)])
# Petfinder API URL
BASE = f'https://api.petfinder.com/v2/'

#### DASH APP LAYOUT

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([

    #Header Text
    html.H1(children="Fetch'd"),

    html.Div(children="Go fetch your next pet!"),

    html.Hr(),

    #Query Layout Div
    html.Div([

            html.Div([
                ###Zipcode + Animal Type Lookup
                html.Div([
                    
                    html.Div(children="Enter Zipcode:", className='twelve columns'),

                    html.Br(),
                    
                    # Zipcode input
                    dcc.Input(id='zipcode-selection', 
                              value='80123', 
                              type='text', 
                              className='twelve columns'),

                    html.Br(),

                    ###Animal type lookup
                    html.Div(children="Enter Animal Type:", className='twelve columns'),

                    html.Br(),

                    # Dropdown for animal type lookup
                    dcc.Dropdown(
                        id='animal-type-selection',
                        options=[{'label':i,'value':i} for i in ["Dog","Cat"]],
                        value="Dog",
                        className='twelve columns'
                    ),

                ], className='six columns'),


                ###Animal gender
                html.Div([
                    
                    html.Div(children="Enter Animal Gender:", className='twelve columns'), 

                    # Dropdown for animal gender lookup
                    dcc.Dropdown(
                        id='animal-gender-selection',
                        options=[{'label':i,'value':i} for i in ["Male","Female","No preference"]],
                        value="No preference"
                    )
                ], className='six columns'),

            ],className='twelve columns',style={'border-style':'dotted'}),


        html.Div(html.Br(),className='six columns'),

        ###Buttons
        html.Div([
                html.Div([
                    # Button to execute search
                    html.Button('Search', id='search-button', n_clicks=0)
                ], className='six columns',style={'text-align':'center'}),
                
                html.Div([
                    # Button to toggle next pet in query
                    html.Button('Next Pet', id='button',n_clicks=0),
                ], className='six columns',style={'text-align':'center'}),
        ], className='twelve columns'),

    ], className='five columns'),

    ###Pet picture + Info Div
    html.Div([
            html.Div([
                #Display current shelter pet picture
                html.Img(id="pet-picture", style={'max-width':'100%','max-height':'100%'})
            ], className='six columns'),

            # Hidden storage for pet query data
            dcc.Store(id='pet-query'),

            html.Div([
                # Display current shelter pet text
                html.Div(id='pet-text',style={'text-align':'center'}),

                dash_table.DataTable(
                    id='pet-table',
                    columns=[{"name": i, "id": i} for i in ['Breed']],
                    style_cell={'textAlign': 'left'},
                    style_as_list_view=True,
                )
            ], className='five columns'),
    ], className='six columns'),
])

# Callback for pet query using dropdowns
@app.callback(
    Output('pet-query', 'data'),
   [Input('search-button', 'n_clicks')],
    [State('animal-type-selection', 'value'), 
    State('animal-gender-selection', 'value'),
    State('zipcode-selection', 'value')])
def update_query(n_clicks, animal_type, gender_value,zipcode):

    ### Local area search for shelter + rescue organizations

    # Request 100 closest organizations to zipcode provided
    get_organizations = requests.get(BASE+f"organizations?location={zipcode}&distance=15&limit=100",headers={"Authorization":"Bearer "+oath.json()['access_token']})

    # INIT dictionary for organizations : organization id
    # This will go into get animals request to petfinder API
    organizations = {}
    for org in get_organizations.json()['organizations']:
        organizations[org['name']]=org['id']

    org_list = ",".join(list(organizations.values()))

    query = {}
    query_string = ""
    #Questions

    #What type of animal are you looking for?
    query['type'] = animal_type.lower()
    query['gender'] = gender_value.lower()

    # Generate query string based on inputs
    for key,values in query.items():
        if values != "" and values != "no preference":
            query_string = query_string+key+"="+values+"&"

    # Pull 50 animal results based on user dropdowns
    get_animals = requests.get(BASE+f"animals?organization={org_list}&{query_string}limit=50",headers={"Authorization":"Bearer "+oath.json()['access_token']})

    # Remove any entries from pet query results that are missing photos
    cleaned_animals = []
    for each in get_animals.json()['animals']:
        if len(each['photos']) != 0:
            cleaned_animals.append(each)

    #Return query results as a json
    return(json.dumps(cleaned_animals))

# Reset number of button clicks
@app.callback(
    Output('button', 'n_clicks'),
    [Input('animal-type-selection', 'value'), 
    Input('animal-gender-selection', 'value')])
def reset(animal_type, gender_value):
    return(0)

# Update currently displayed shelter pet picture
@app.callback(
    Output('pet-picture', 'src'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_picture(query, clicks):

    # Read in pet query results
    loaded = json.loads(query)

    #Evaluate the number of pet results in the query
    query_length = len(loaded)-1

    #Show pet picture of current shelter pet.
    #If no results, show picture of cacti.
    if query_length <= 0 or query_length == None:
        src="https://cdn.shopify.com/s/files/1/2203/9263/products/96e0977de16d61248b634d1fa937bd8d.jpg?v=1538610080"
    else:
        
        #Integer divide the number of clicks by the total query length
        #To determine if a user has viewed all pets
        looped = int(clicks) // query_length
        
        #Subtract number of total clicks to find index of pet that should
        # be displayed
        number = int(clicks) - looped * query_length
        
        src=loaded[number]['photos'][0]['medium']
    return(src)

# Update current shelter pet text
@app.callback(
    Output('pet-text', 'children'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_text(query, clicks):
    # Read in pet query results
    loaded = json.loads(query)

    #Evaluate the number of pet results in the query
    query_length = len(loaded)-1

    #Show pet text of current shelter pet.
    #If no results, print alt message
    if query_length <= 0 or query_length == None:
        return("No results :(")
    else:
        #Integer divide the number of clicks by the total query length
        #To determine if a user has viewed all pets   
        looped = int(clicks) // query_length
        
        #Subtract number of total clicks to find index of pet that should
        # be displayed
        number = int(clicks) - looped * query_length
        return("Meet ",loaded[number]['name'].title(),"!")

# Update current shelter pet data table
@app.callback(
    Output('pet-table', 'data'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_table(query, clicks):
    # Read in pet query results
    loaded = json.loads(query)

    #Evaluate the number of pet results in the query
    query_length = len(loaded)-1

    #Show pet text of current shelter pet.
    #If no results, print alt message
    if query_length <= 0 or query_length == None:
        return("No results :(")
    else:
        #Integer divide the number of clicks by the total query length
        #To determine if a user has viewed all pets   
        looped = int(clicks) // query_length
        
        #Subtract number of total clicks to find index of pet that should
        # be displayed
        number = int(clicks) - looped * query_length

        query_results = pd.DataFrame({'Breed':[loaded[number]['breeds']['primary'].title()]})

        return(query_results.to_dict('records'))

# Run server
if __name__ == '__main__':
    app.run_server()