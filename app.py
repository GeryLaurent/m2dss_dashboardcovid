# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 10:43:51 2020

@author: Gery
"""

# Libraries import part

import dash
import dash_core_components as dcc
import dash_html_components as html


import plotly.express as px
import pandas as pd
pd.options.mode.chained_assignment = None
import datetime
import json
import requests, zipfile
from io import BytesIO

########################################
# Data collection & Data management
########################################

# Open geojson department data for France
#with open("D:\CovidProject\departements.geojson") as f:
with open("departements.geojson") as f:
    franceMap = json.load(f)
   
sortedMap = dict(franceMap)
sortedMap['features'] = sorted(franceMap['features'], key=lambda x: x['properties']['code'])

# Export Department information
df = pd.read_csv("https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv")
dfDepartment = df[df['maille_code'].str.contains("DEP")]
dfDepartment['code_dep'] = dfDepartment['maille_code'].str.split('-').str[1]
dfDepartmentMet = dfDepartment[~dfDepartment['code_dep'].isin(['971','972','973','974','975','976','977','978']) ] # Remove overseas departments


# Données INSEE décès par département [1er mars au 31 juillet]
zipLink = requests.get('https://www.insee.fr/fr/statistiques/fichier/4487988/2020-07-31_deces_quotidiens_departement_csv.zip', stream=True)
zp = zipfile.ZipFile(BytesIO(zipLink.content)) # Read zip file
dfDeces = pd.read_csv(zp.open("2020-31-07_deces_quotidiens_departement_csv.csv"),sep=",")
dfDeces['code_dep'] = dfDeces['Zone'].str.split('_').str[1]
dfDecesMet = dfDeces[~dfDeces['code_dep'].isin(['971','972','973','974','975','976','977','978']) ].dropna(subset=['code_dep'])


# Données hospitalières par département [total]
dfHospit = pd.read_csv("https://www.data.gouv.fr/en/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",sep=";")
dfHospitMet = dfHospit[~dfHospit['dep'].isin(['971','972','973','974','976']) ]
dfHospitMet['jour'] = dfHospitMet['jour'].apply(lambda x: x if x.startswith('2020') else datetime.datetime.strptime(x, '%d/%m/%Y').strftime('%Y-%m-%d')) # Date conversion to correct datetime errors in the data
# Données hospitalières quotidiennes par département [nouveaux]
dfHospitNew = pd.read_csv("https://www.data.gouv.fr/en/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",sep=";")
dfHospitNewMet = dfHospitNew[~dfHospitNew['dep'].isin(['971','972','973','974','975','976','977','978']) ]
dfHospitNewMet['jour'] = dfHospitNewMet['jour'].apply(lambda x: x if x.startswith('2020') else datetime.datetime.strptime(x, '%d/%m/%Y').strftime('%Y-%m-%d'))
# Données test dépistage par département [ avant 29 mai 2020]
# Metadonnées catégories age
"""
Code tranches d'age
0	tous âges
A	moins de 15 ans
B	15-44 ans
C	45-64 ans
D	65-74 ans
E	75 et plus
"""

dfDepistage = pd.read_csv("https://www.data.gouv.fr/en/datasets/r/b4ea7b4b-b7d1-4885-a099-71852291ff20",sep=";")
dfDepistageMet = dfDepistage[~dfDepistage['dep'].isin(['971','972','973','974','975','976','977','978']) ]

# Données test dépistage par département [ après le 13 mai 2020]
# Metadonnées catégories age
"""
Code tranches d'age
0	tous âges
9	0-9 ans ?
19	10-19 ans ?
etc.
"""
dfDepistageBis = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675",sep=";")
dfDepistageBisMet = dfDepistageBis[~dfDepistageBis['dep'].isin(['971','972','973','974','975','976','977','978']) ]
dfDepistageBisMet = dfDepistageBisMet[dfDepistageBisMet['cl_age90'] == 0]
dfDepistageBisMet = dfDepistageBisMet.drop(['cl_age90'], axis=1)
# Fusion des deux tables

dfDepistageMetFormatted = dfDepistageMet.rename(columns={'nb_test': 'T','nb_pos':'P'})
dfDepistageMetFormatted  = dfDepistageMetFormatted[dfDepistageMetFormatted['clage_covid'] == '0']
dfDepistageMetFormatted = dfDepistageMetFormatted.drop(['clage_covid','nb_test_h','nb_pos_h','nb_test_f','nb_pos_f'], axis=1)

dfDepistageMetFused = pd.concat([dfDepistageMetFormatted, dfDepistageBisMet], ignore_index=True)


# Données test dépistage France entière [ après le 13 mai 2020]
dfDepistageFranceBis = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/dd0de5d9-b5a5-4503-930a-7b08dc0adc7c",sep=";")

# Données urgences par département
dfUrgence = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/eceb9fb4-3ebc-4da3-828d-f5939712600a",sep=";")
dfUrgenceMet = dfUrgence[~dfUrgence['dep'].isin(['971','972','973','974','976']) ]
# Données urgences France entière
dfUrgenceFrance = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/219427ba-7e90-4eb1-9ac7-4de2e7e2112c",sep=";")

# Données taux incidence par département
# Le taux d'incidence correspond au nombre de tests positifs pour 100.000 habitants. Il est calculé de la manière suivante : (100000 * nombre de cas positif) / Population

dfIncidence = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/4180a181-a648-402b-92e4-f7574647afa6",sep=";")
dfIncidenceMet = dfIncidence[~dfIncidence['dep'].isin(['971','972','973','974','976']) ]


dfDepartmentMet = dfDepartmentMet.sort_values(by=['code_dep'])

# Dictionnaire de liaison des départements et de leur code
codeDepList = dfDepartmentMet['code_dep'].unique()
codeDepName = dfDepartmentMet['maille_nom'].unique()
dictDepLink = dict(zip(codeDepList,codeDepName))
dictDepLink.update( {'FR': 'France métropolitaine'})
"""
RESUME DES INFORMATIONS FIABLES A DISPOSITION PAR DEPARTEMENT
A partir du 13 mai 2020
- P: nombre de tests positifs
- T: nombre de tests réalisés
- tx_std: taux d'incidence: (100000 * nombre de cas positif) / Population
- hosp: nombre total de patients hospitalisés à ce jour
- rea: nombre total de patients en réanimation à ce jour
- dc: nombre total de patients décédés à ce jour
- incid_hosp: nombre de nouveaux patients hospitalisés dans la journée
- incid_rea: nombre de nouveaux patients en réanimation dans la journée
- incid_dc: nombre de nouveaux patients décédés dans la journée
"""

# Nombre de tests positifs, testés et incidence
dfDepistageBisMetCleaned = dfDepistageBisMet.drop(['P'], axis=1)
df_1 = pd.merge(dfDepistageBisMetCleaned, dfIncidenceMet, how='left', on=['dep','jour'])
# Calcul du taux de positivité: (nombre de test positif / nombre de test réalisé)*100
df_1['tx_pos'] = df_1['P'] / df_1['T']

# Nombre de patients hospitalisés, en réanimation pour Covid-19
dfHospitMetCleaned = dfHospitMet[dfHospitMet['sexe'] == 0].drop(['sexe','rad'], axis=1).sort_values(by=['dep','jour'])
dfHospitNewMetCleaned = dfHospitNewMet.drop(['incid_rad'], axis=1).sort_values(by=['dep','jour'])
df_2 = pd.merge(dfHospitMetCleaned, dfHospitNewMetCleaned, how='left', on=['dep','jour'])

# Merge des deux dataframes en un dataframe centralisé
dfMain = pd.merge(df_1, df_2, how='left', on=['dep','jour'])

dateList = dfMain['jour'].unique()
firstDay = dateList[0]
lastDay = dateList[-1]

# Somme des colonnes pour avoir les chiffres pour la France Métropolitaine
dfMainSumFr = dfMain.drop(['dep','tx_std','incid_hosp','incid_rea','incid_dc','tx_pos'], axis=1).groupby(['jour']).sum(min_count=len(codeDepList)-1).reset_index()
dfMainSumFr['tx_pos'] = dfMainSumFr['P'] / dfMainSumFr['T']
dfMainSumFr['dep'] = "FR"

# Merge des deux dataframes en un dataframe centralisé
dfMainIncFr = pd.concat([dfMainSumFr, dfMain.drop(['tx_std','incid_hosp','incid_rea','incid_dc'], axis=1)])
dfMainIncFr['timestamp']=pd.to_datetime(dfMainIncFr['jour'])
dfMainIncFr['serialtime']=[(d-datetime.datetime(1970,1,1)).days for d in dfMainIncFr['timestamp']]


########################################
# Data visualisation
########################################

#### Génération des courbes par défaut à l'ouverture du dashboard

# Courbe du taux de positivité du test de dépistage avec courbe de tendance
figTl = px.scatter(dfMainIncFr[dfMainIncFr['dep'] == "FR"], x="serialtime", y="tx_pos",title="Taux de positivité du test de dépistage", trendline="ols", trendline_color_override='#ff9999')
trendlineTl = figTl.data[1]
figI = px.line(dfMainIncFr[dfMainIncFr['dep'] == "FR"], x="serialtime", y="tx_pos",title="Taux de positivité du test de dépistage")
figI.add_trace(trendlineTl)
figI.update_xaxes(tickangle=45,
                tickmode = 'array',
                tickvals = dfMainIncFr[dfMainIncFr['dep'] == "FR"]['serialtime'][1::7],
                ticktext= dfMainIncFr[dfMainIncFr['dep'] == "FR"]['jour'][1::7])
figI.update_layout(yaxis_tickformat = '%')
figI.update_xaxes(title_text='')
figI.update_yaxes(title_text='Taux de positivité')

# Courbe du nombre actuel d'hospitalisation
figH = px.line(dfMainIncFr[dfMainIncFr['dep'] == "FR"], x="jour", y="hosp", title="Nombre actuel d'hospitalisation pour covid-19")
figH.update_xaxes(title_text='')
figH.update_yaxes(title_text="nombre de patients")

# Courbe du nombre actuel de réanimation
figR = px.line(dfMainIncFr[dfMainIncFr['dep'] == "FR"], x="jour", y="rea", title="Nombre actuel de patients covid-19 en réanimation")
figR.update_xaxes(title_text='')
figR.update_yaxes(title_text="nombre de patients")

# Courbe du nombre cumulé de décès
figDc = px.line(dfMainIncFr[dfMainIncFr['dep'] == "FR"], x="jour", y="dc", title="Nombre de décès cumulé à l'hôpital lié au covid-19")
figDc.update_xaxes(title_text='')
figDc.update_yaxes(title_text="nombre de décès")

########################################
# Initialisation de Dash et mise en page
########################################

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(className="grid-container",
                      style={'height':'100vh'},
                      children=[
    dcc.Markdown(className="Title", children='**Tableau de bord Covid-19: situation en France métropolitaine**'),

    html.Div(className="Filters", 
             children=[html.Div(className="Filter1",
                                children=[
                                    'Choix de la date: ',
                                    dcc.DatePickerSingle( # Interactive calendar for day selection
                                        id='datePicker',
                                        min_date_allowed=firstDay,
                                        max_date_allowed=lastDay,
                                        initial_visible_month=lastDay,
                                        date=lastDay
                                        )
                                ]),
                       html.Div(className="Filter2",
                                children=[
                                    'Choix de la variable: ',
                                    dcc.RadioItems( # Tick box for variable selection
                                        id='variablePicker',
                                        options=[
                                            {'label': "Décès quotidien à l'hôpital", 'value': 'incid_dc'},
                                            {'label': "Taux d'incidence", 'value': 'tx_std'},
                                            {'label': 'Nouvelles Hospitalisations', 'value': 'incid_hosp'},
                                            {'label': 'Nouvelles Réanimations', 'value': 'incid_rea'} 
                                        ],
                                        value='incid_dc',
                                        labelStyle={'display': 'inline-block'}
                                        )
                                    ])
                       ]
             ),
    
    dcc.Markdown(className="Subtitle", 
             id='dep_selected'
             ),

    dcc.Graph( # Carte de France métropolitaine et départements
        className="Map",
        id='mapFr'
    ),
    dcc.Graph( # Courbe du taux de positivité du test de dépistage avec courbe de tendance
        className="Graph1",
        id='graphTest',
        figure=figTl
    ),
    dcc.Graph( # Courbe du nombre actuel d'hospitalisation
        className="Graph2",
        id='graphHospit',
        figure=figH
    ),
    dcc.Graph( # Courbe du nombre actuel de réanimation
        className="Graph3",
        id='graphRea',
        figure=figR
    ),
    dcc.Graph( # Courbe du nombre cumulé de décès
        className="Graph4",
        id='graphDc',
        figure=figDc
    ),
    dcc.Markdown(className="Author", children='Dashboard créé par Géry LAURENT'),
    dcc.Markdown(className="Source", children='''Source: [data.gouv.fr](https://www.data.gouv.fr)'''),    
])

@app.callback(
    dash.dependencies.Output('mapFr', 'figure'),
    [dash.dependencies.Input('datePicker', 'date'),
     dash.dependencies.Input('variablePicker','value')])
def update_graph(day_value,variable): # Function to update map based on selected variable
    
    dictOptions = {
        'incid_dc': {'color':['#ffffff', '#ff0000'],
                     'label': "Décès Quotidien"},
        'tx_std': {'color':['#ffffff', '#8000ff'],
                     'label': "Taux d'incidence"},
        'incid_hosp': {'color':['#ffffff', '#0066ff'],
                     'label': "Nouvelles Hospitalisations"},
        'incid_rea': {'color':['#ffffff', '#ff6600'],
                     'label': "Nouvelles Réanimations"}
        }
    dfMapVariable = dfMain[dfMain['jour'] == day_value].filter(['dep',variable])

    figMap = px.choropleth_mapbox(dfMapVariable, geojson=sortedMap, locations='dep', featureidkey = 'properties.code', color=variable,
                               color_continuous_scale=dictOptions[variable]['color'],
                               mapbox_style="carto-positron",
                               zoom=4.7, center = {"lat": 46.5, "lon": 2.5},
                               opacity=0.7,
                               labels={'dep':'code du départment',variable : dictOptions[variable]['label']}
                              )
    figMap.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                         clickmode='event+select')
    
    return figMap

@app.callback(
    dash.dependencies.Output('dep_selected', 'children'),
    [dash.dependencies.Input('mapFr', 'selectedData')])
def display_selected_data(selectedData): # Function to change subtitle based on selected department
    if selectedData is None:
        dep = "FR"
    else:
        dep = selectedData['points'][0]['location']
        
    depName = dictDepLink[dep]
    popNb = dfMainIncFr[dfMainIncFr['dep'] == dep]['pop'].unique()[0]
    
    text = "**Zone sélectionnée: **" + depName + " ( " + dep + " )" + "** - Population: **" + str(popNb)
    return text

@app.callback(
    dash.dependencies.Output('graphTest', 'figure'),
    [dash.dependencies.Input('mapFr', 'selectedData')])
def update_curve1(selectedData):     # Function to update curve 1 based on selected department

    if selectedData is None:
        dep = "FR"
    else:
        dep = selectedData['points'][0]['location']
        
    figTl = px.scatter(dfMainIncFr[dfMainIncFr['dep'] == dep], x="serialtime", y="tx_pos",title="Taux de positivité du test de dépistage", trendline="ols", trendline_color_override='#ff9999')
    trendlineTl = figTl.data[1]
    figI = px.line(dfMainIncFr[dfMainIncFr['dep'] == dep], x="serialtime", y="tx_pos",title="Taux de positivité du test de dépistage")
    figI.add_trace(trendlineTl)
    figI.update_xaxes(tickangle=45,
                     tickmode = 'array',
                     tickvals = dfMainIncFr[dfMainIncFr['dep'] == dep]['serialtime'][1::7],
                     ticktext= dfMainIncFr[dfMainIncFr['dep'] == dep]['jour'][1::7])
    figI.update_layout(yaxis_tickformat = '%')
    figI.update_xaxes(title_text='')
    figI.update_yaxes(title_text='Taux de positivité')
    return figI

@app.callback(
    dash.dependencies.Output('graphHospit', 'figure'),
    [dash.dependencies.Input('mapFr', 'selectedData')])
def update_curve2(selectedData):   # Function to update curve 2 based on selected department  

    if selectedData is None:
        dep = "FR"
    else:
        dep = selectedData['points'][0]['location']
        
    figH = px.line(dfMainIncFr[dfMainIncFr['dep'] == dep], x="jour", y="hosp", title="Nombre actuel d'hospitalisation pour covid-19")
    figH.update_xaxes(title_text='')
    figH.update_yaxes(title_text="nombre de patients")
    return figH

@app.callback(
    dash.dependencies.Output('graphRea', 'figure'),
    [dash.dependencies.Input('mapFr', 'selectedData')])
def update_curve3(selectedData):  # Function to update curve 3 based on selected department  

    if selectedData is None:
        dep = "FR"
    else:
        dep = selectedData['points'][0]['location']
        
    figR = px.line(dfMainIncFr[dfMainIncFr['dep'] == dep], x="jour", y="rea", title="Nombre actuel de patients covid-19 en réanimation")
    figR.update_xaxes(title_text='')
    figR.update_yaxes(title_text="nombre de patients")
    return figR

@app.callback(
    dash.dependencies.Output('graphDc', 'figure'),
    [dash.dependencies.Input('mapFr', 'selectedData')])
def update_curve4(selectedData):  # Function to update curve 4 based on selected department  

    if selectedData is None:
        dep = "FR"
    else:
        dep = selectedData['points'][0]['location']
        
    figDc = px.line(dfMainIncFr[dfMainIncFr['dep'] == dep], x="jour", y="dc", title="Nombre de décès cumulé à l'hôpital lié au covid-19")
    figDc.update_xaxes(title_text='')
    figDc.update_yaxes(title_text="nombre de décès")
    return figDc

if __name__ == '__main__':
    app.run_server(debug=True)