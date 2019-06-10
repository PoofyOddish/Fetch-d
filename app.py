# Petfinder - Fetch'd Application Code
# Features to add:
# Zipcode input


#Import necessary packages
import requests
import json
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# API credentials
# API key and secret saved in Heroku
api_key = os.environ['PETFINDER_KEY']
api_secret = os.environ['PETFINDER_SECRET']

# OATH for Petfinder session
oath = requests.post('https://api.petfinder.com/v2/oauth2/token/',data=[('grant_type','client_credentials'),
                                                                 ('client_id',api_key),
                                                                ('client_secret',api_secret)])
# Petfinder API URL
BASE = f'https://api.petfinder.com/v2/'

### Local area search for shelter + rescue organizations
# Manually defined zipcode - will replace later
zipcode = 80123

# Request 100 closest organizations to zipcode provided
get_organizations = requests.get(BASE+f"organizations?location={zipcode}&distance=10&limit=100",headers={"Authorization":"Bearer "+oath.json()['access_token']})

# INIT dictionary for organizations : organization id
# This will go into get animals request to petfinder API
organizations = {}
for org in get_organizations.json()['organizations']:
    organizations[org['name']]=org['id']

org_list = ",".join(list(organizations.values()))


#### DASH APP LAYOUT

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([

    html.H1(children="Littleton Petfinder Results"),

    html.Div(children="I'm helping!"),

    html.Div([
        # Dropdown for animal type lookup
        dcc.Dropdown(
            id='animal-type-selection',
            options=[{'label':i,'value':i} for i in ["Dog","Cat"]],
            value="Dog"
        ),
        
        # Dropdown for animal gender lookup
        dcc.Dropdown(
            id='animal-gender-selection',
            options=[{'label':i,'value':i} for i in ["Male","Female","No preference"]],
            value="No preference"
        ),
    ]),

    html.Div([
        html.Div(
            # Button to toggle next pet in query
            html.Button('Next Pet', id='button'),)
    ]),

    html.Div([

        #Display current shelter pet picture
        html.Img(
            id="pet-picture"
        )
    ]),
    # Hidden storage for pet query data
    dcc.Store(id='pet-query'),

    html.Div([
        # Display current shelter pet text
        html.Div(id='pet-text')
    ])
])

# Callback for pet query using dropdowns
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
def update_picture(query,clicks):

    # Read in pet query results
    loaded = json.loads(query)

    ##### JSON indexing calculations

    #If there are no button clicks, initialize value to 0
    if clicks == None:
        clicks = 0

    #Evaluate the number of pet results in the query
    query_length = len(loaded)-1

    #Integer divide the number of clicks by the total query length
    #To determine if a user has viewed all pets
    looped = clicks // query_length

    #Subtract number of total clicks to find index of pet that should
    # be displayed
    number = clicks - looped * query_length
    #####

    #Show pet picture of current shelter pet.
    #If no results, show picture of cacti.
    if query_length < 0 or query_length == None:
        src="https://cdn.shopify.com/s/files/1/2203/9263/products/96e0977de16d61248b634d1fa937bd8d.jpg?v=1538610080"
    else:
        src=loaded[number]['photos'][0]['medium']
    return(src)

# Update current shelter pet text
@app.callback(
    Output('pet-text', 'children'),
    [Input('pet-query', 'data'),
    Input('button', 'n_clicks')])
def update_text(query,clicks):

    # Read in pet query results
    loaded = json.loads(query)

    ##### JSON indexing calculations

    #If there are no button clicks, initialize value to 0
    if clicks == None:
        clicks = 0

    #Evaluate the number of pet results in the query
    query_length = len(loaded)-1

    #Integer divide the number of clicks by the total query length
    #To determine if a user has viewed all pets   
    looped = clicks // query_length

    #Subtract number of total clicks to find index of pet that should
    # be displayed
    number = clicks - looped * query_length

    #####

    #Show pet text of current shelter pet.
    #If no results, print alt message
    if query_length < 0 or query_length == None:
        return("No results :(")
    else:
        return("Hey look, it's ",loaded[number]['name'].title(),"!")

# Run server
if __name__ == '__main__':
    app.run_server()