# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 10:43:51 2020

@author: Gery
"""

import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.express as px
import pandas as pd
import datetime
import json
import requests, zipfile
from io import BytesIO

with open("departements.geojson") as f:
    franceMap = json.load(f)
   
sortedMap = dict(franceMap)
sortedMap['features'] = sorted(franceMap['features'], key=lambda x: x['properties']['code'])

df = pd.read_csv("https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv")
dfDepartment = df[df['maille_code'].str.contains("DEP")]
dfDepartment['code_dep'] = dfDepartment['maille_code'].str.split('-').str[1]
dfDepartmentMet = dfDepartment[~dfDepartment['code_dep'].isin(['971','972','973','974','976']) ]


# Données INSEE décès par département [1er mars au 31 juillet]
zipLink = requests.get('https://www.insee.fr/fr/statistiques/fichier/4487988/2020-07-31_deces_quotidiens_departement_csv.zip', stream=True)
zp = zipfile.ZipFile(BytesIO(zipLink.content))
dfDeces = pd.read_csv(zp.open("2020-31-07_deces_quotidiens_departement_csv.csv"),sep=",")
dfDeces['code_dep'] = dfDeces['Zone'].str.split('_').str[1]
dfDecesMet = dfDeces[~dfDeces['code_dep'].isin(['971','972','973','974','976']) ].dropna(subset=['code_dep'])


# Données hospitalières par département [total]
dfHospit = pd.read_csv("https://www.data.gouv.fr/en/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",sep=";")
dfHospitMet = dfHospit[~dfHospit['dep'].isin(['971','972','973','974','976']) ]

# Données hospitalières quotidiennes par département [nouveaux]
dfHospitNew = pd.read_csv("https://www.data.gouv.fr/en/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",sep=";")
dfHospitNewMet = dfHospitNew[~dfHospitNew['dep'].isin(['971','972','973','974','976']) ]

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
dfDepistageMet = dfDepistage[~dfDepistage['dep'].isin(['971','972','973','974','976']) ]

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
dfDepistageBisMet = dfDepistageBis[~dfDepistageBis['dep'].isin(['971','972','973','974','976']) ]
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
codeDepList = dfDepartmentMet['code_dep'].unique()
codeDepName = dfDepartmentMet['maille_nom'].unique()

"""
RESUME DES INFORMATIONS FIABLES A DISPOSITION PAR DEPARTEMENT
A partir du 13 mai 2020
- P: nombre de tests positifs
- T: nombre de tests réalisés
- tx_std: taux d'incidence: (100000 * nombre de cas positif) / Population
- hosp: nombre total de patients hospitalisés à ce jour
- rea: nombre total de patients en réanimation à ce jour
- dc: nombre total de patients décédés à ce jour
"""

# Nombre de tests positifs, testés et incidence
dfDepistageBisMetCleaned = dfDepistageBisMet.drop(['P'], axis=1)
df_1 = pd.merge(dfDepistageBisMetCleaned, dfIncidenceMet, how='left', on=['dep','jour']).drop(['pop'], axis=1)
# Calcul du taux de positivité: (nombre de test positif / nombre de test réalisé)*100
df_1['tx_pos'] = df_1['P'] / df_1['T'] * 100

# Nombre de patients hospitalisés, en réanimation pour Covid-19
dfHospitMetCleaned = dfHospitMet[dfHospitMet['sexe'] == 0].drop(['sexe','rad'], axis=1).sort_values(by=['dep','jour'])
dfHospitNewMetCleaned = dfHospitNewMet.drop(['incid_rad'], axis=1).sort_values(by=['dep','jour'])
df_2 = pd.merge(dfHospitMetCleaned, dfHospitNewMetCleaned, how='left', on=['dep','jour'])

# Merge des deux dataframes en un dataframe centralisé
dfMain = pd.merge(df_1, df_2, how='left', on=['dep','jour'])

dateList = dfMain['jour'].unique()
firstDay = dateList[0]
lastDay = dateList[-1]




external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = ['D:\chrcode\Dashboard_Demo\Prototype_indicateur\Style\Styles_proto_activite.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Génération de la carte de France par département
df_1308 = dfMain[dfMain['jour']=="2020-08-13"]

df1308_deces = df_1308.filter(['dep','incid_dc'])

import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"
fig = px.choropleth_mapbox(df1308_deces, geojson=sortedMap, locations='dep', featureidkey = 'properties.code', color='incid_dc',
                           color_continuous_scale=['#ffffff', '#ff0000'],
                           mapbox_style="carto-positron",
                           zoom=5.4, center = {"lat": 46.5, "lon": 1},
                           opacity=0.5,
                           labels={'dep':'code du départment','incid_dc':'nombre de décès'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

app.layout = html.Div(children=[
    html.H1(children='Nombre de décès quotidien'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
