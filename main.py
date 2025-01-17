import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
from datetime import datetime
import os

baseURL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

tickFont = {'size': 12, 'color': 'rgb(30,30,30)', 'family': 'Courier New, monospace'}
app = dash.Dash(__name__)
# app.config.suppress_callback_exceptions = True
server = app.server
all_data = None
countries = None


def load_single_data(fileName, columnName):
    data = pd.read_csv(baseURL + fileName) \
        .drop(['Lat', 'Long'], axis=1) \
        .melt(id_vars=['Province/State', 'Country/Region'], var_name='date', value_name=columnName) \
        .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


def load_US_confirmed_data(file_name, column_name):
    data = pd.read_csv(baseURL + file_name) \
        .drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Lat', 'Long_', 'Combined_Key'], axis=1) \
        .groupby(by=['Country_Region', 'Province_State']) \
        .sum() \
        .reset_index()

    data = data.melt(id_vars=['Country_Region', 'Province_State'], var_name='date', value_name=column_name) \
        .fillna('<all>')
    data.rename(columns={'Country_Region': 'Country/Region', 'Province_State': 'Province/State'}, inplace=True)
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


def load_US_deaths_data(file_name, column_name):
    data = pd.read_csv(baseURL + file_name) \
        .drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Lat', 'Long_', 'Combined_Key', 'Population'], axis=1) \
        .groupby(by=['Country_Region', 'Province_State']) \
        .sum() \
        .reset_index()

    data = data.melt(id_vars=['Country_Region', 'Province_State'], var_name='date', value_name=column_name) \
        .fillna('<all>')
    data.rename(columns={'Country_Region': 'Country/Region', 'Province_State': 'Province/State'}, inplace=True)
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


def load_US_latest_data():
    confirmed_data = load_US_confirmed_data('time_series_covid19_confirmed_US.csv', 'CumConfirmed')
    deaths_data = load_US_deaths_data('time_series_covid19_deaths_US.csv', 'CumDeaths')
    _data = confirmed_data.merge(deaths_data)
    _data['CumConfirmed'] = _data['CumConfirmed'].astype(float)
    _data['CumDeaths'] = _data['CumDeaths'].astype(float)
    _data['CumRecovered'] = 0  # not available
    return _data


def get_active_cases(data: pd.DataFrame):
    data['CumActive'] = data['CumConfirmed'] - data['CumDeaths'] - data['CumRecovered']
    return data


def load_global_latest_data():
    # load global data
    confirmed_data = load_single_data('time_series_covid19_confirmed_global.csv', 'CumConfirmed')
    deaths_data = load_single_data('time_series_covid19_deaths_global.csv', 'CumDeaths')
    recovered_data = load_single_data('time_series_covid19_recovered_global.csv', 'CumRecovered')
    _data = confirmed_data.merge(deaths_data).merge(recovered_data)
    _data['CumConfirmed'] = _data['CumConfirmed'].astype(float)
    _data['CumDeaths'] = _data['CumDeaths'].astype(float)
    _data['CumRecovered'] = _data['CumRecovered'].astype(float)

    # load US data
    us_data = load_US_latest_data()

    # combine the two dataset
    # _data = _data[_data['Country/Region'] != 'US']
    _data = _data.append(us_data, sort=False)
    _data = get_active_cases(_data)
    return _data


def get_timenow():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def app_layout():
    global all_data, countries
    all_data = load_global_latest_data()
    countries = all_data['Country/Region'].unique()
    countries = np.append(countries, '<all>')
    countries.sort()
    return html.Div(
        id='main_layout',
        style={'font-family': 'Courier New, monospace'},
        children=[
            html.Div(f'Refresh the page to update (Last Updated {str(get_timenow())})', id='update-time',
                     style={'color': '#6d7073'}),
            html.H1('Evolution of the Coronavirus (COVID-19)'),
            html.Div(className='row', children=[
                html.Div(className='four columns', children=[
                    html.H5('Country'),
                    dcc.Dropdown(
                        id='country',
                        options=[{'label': c, 'value': c} for c in countries],
                        value='<all>'
                    )
                ]),
                html.Div(className='four columns', children=[
                    html.H5('State / Province'),
                    dcc.Dropdown(
                        id='state',
                        value='<all>'
                    )
                ]),
                html.Div(className='four columns', children=[
                    html.H5('Selected Metrics'),
                    dcc.Checklist(
                        id='metrics',
                        options=[{'label': m, 'value': m} for m in ['Confirmed', 'Deaths', 'Recovered', 'Active']],
                        value=['Confirmed', 'Deaths', 'Recovered', 'Active']
                    )
                ])
            ]),
            dcc.Graph(
                id='plot_new_metrics',
                config={'displayModeBar': False},
            ),
            html.Br(),
            dcc.Graph(
                id='plot_cum_metrics',
                config={'displayModeBar': False}
            ),
            html.Br(),
            html.H6(
                html.A('Powered By COVID-19 Data Repository by Johns Hopkins CSSE',
                       style={'color': '#1c1b1b'},
                       href='https://github.com/CSSEGISandData/COVID-19'
                       )
            )
        ])


def data_by_country(country):
    if country == '<all>':
        return all_data.loc[~((all_data['Country/Region'] == 'US') & (all_data['Province/State'] != '<all>')), :]\
            .drop('Country/Region', axis=1)
    else:
        return all_data.loc[all_data['Country/Region'] == country].drop('Country/Region', axis=1)


def data_by_state(data: pd.DataFrame, country: str, state: str):
    if state == '<all>':
        if country == 'US':
            data = data.loc[data['Province/State'] == '<all>']
            return data.drop('Province/State', axis=1)
        else:
            return data.drop('Province/State', axis=1).groupby('date').sum().reset_index()
    else:
        if country == 'US':
            data = data.loc[data['Province/State'] != '<all>']
            return data.loc[data['Province/State'] == state]
        else:
            return data.loc[data['Province/State'] == state]


def accumulative_data(country, state):
    data = data_by_country(country)
    data = data_by_state(data, country, state)
    data = data.fillna(0)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data


def daily_change_data(data):
    data['NewConfirmed'] = data['CumConfirmed'].diff()
    data['NewDeaths'] = data['CumDeaths'].diff()
    data['NewRecovered'] = data['CumRecovered'].diff()
    data['NewActive'] = data['CumActive'].diff()
    return data.dropna()


def barchart(data, metrics, prefix='', yaxisTitle=''):
    figure = go.Figure(data=[
        go.Bar(
            name=metric, x=data.date, y=data[prefix + metric],
            marker_line_color='rgb(0,0,0)', marker_line_width=1,
            marker_color={'Deaths': 'rgb(200,30,30)', 'Recovered': 'rgb(30,200,30)',
                          'Confirmed': 'rgb(100,140,240)', 'Active': 'rgb(255,191,0)'}[
                metric]
        ) for metric in metrics
    ])
    figure.update_layout(
        barmode='group', legend=dict(x=.05, y=0.95, font={'size': 15}, bgcolor='rgba(240,240,240,0.5)'),
        plot_bgcolor='#FFFFFF', font=tickFont) \
        .update_xaxes(
        title='', tickangle=-90, type='category', showgrid=True, gridcolor='#DDDDDD',
        tickfont=tickFont, ticktext=data.dateStr, tickvals=data.date) \
        .update_yaxes(
        title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD')
    return figure


app.layout = app_layout


@app.callback(
    [Output('state', 'options'), Output('state', 'value')],
    [Input('country', 'value')]
)
def update_states(country):
    states = list(all_data.loc[all_data['Country/Region'] == country]['Province/State'].unique())
    states.insert(0, '<all>')
    states.sort()
    state_options = [{'label': s, 'value': s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value


@app.callback(
    [
        Output('plot_new_metrics', 'figure'),
        Output('plot_cum_metrics', 'figure'),
    ],
    [
        Input('country', 'value'),
        Input('state', 'value'),
        Input('metrics', 'value'),
    ]
)
def update_plot_new_metrics(country, state, metrics):
    data = accumulative_data(country, state)
    new_cases_data = daily_change_data(data)
    new_chart = barchart(new_cases_data, metrics, prefix='New', yaxisTitle='New Cases per Day')
    cum_chart = barchart(data, metrics, prefix='Cum', yaxisTitle='Accumulated Total Cases')
    return new_chart, cum_chart


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=os.getenv('DEBUG', False))
