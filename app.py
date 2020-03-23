import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np

baseURL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

tickFont = {'size': 12, 'color': 'rgb(30,30,30)', 'family': 'Courier New, monospace'}


def load_data(fileName, columnName):
    data = pd.read_csv(baseURL + fileName) \
        .drop(['Lat', 'Long'], axis=1) \
        .melt(id_vars=['Province/State', 'Country/Region'], var_name='date', value_name=columnName) \
        .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


confirmed_data = load_data('time_series_19-covid-Confirmed.csv', 'CumConfirmed')
deaths_data = load_data('time_series_19-covid-Deaths.csv', 'CumDeaths')
recovered_data = load_data('time_series_19-covid-Recovered.csv', 'CumRecovered')
all_data = confirmed_data.merge(deaths_data).merge(recovered_data)

countries = all_data['Country/Region'].unique()
countries = np.append(countries, '<all>')
countries.sort()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    style={'font-family': 'Courier New, monospace'},
    children=[
        html.H1('Case History of the Coronavirus (COVID-19)'),
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
                    options=[{'label': m, 'value': m} for m in ['Confirmed', 'Deaths', 'Recovered']],
                    value=['Confirmed', 'Deaths']
                )
            ])
        ]),
        dcc.Graph(
            id='plot_new_metrics',
            config={'displayModeBar': False}
        ),
        dcc.Graph(
            id='plot_cum_metrics',
            config={'displayModeBar': False}
        )
    ])


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


def data_by_country(country):
    if country == '<all>':
        return all_data.drop('Country/Region', axis=1)
    else:
        data = all_data.loc[all_data['Country/Region'] == country]
        return data.drop('Country/Region', axis=1)


def accumulative_data(country, state):
    data = data_by_country(country)
    if state == '<all>':
        data = data.drop('Province/State', axis=1).groupby('date').sum().reset_index()
    else:
        data = data.loc[data['Province/State'] == state]
    data = data.fillna(0)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data


def daily_change_data(data):
    data['NewConfirmed'] = data['CumConfirmed'].diff()
    data['NewDeaths'] = data['CumDeaths'].diff()
    data['NewRecovered'] = data['CumRecovered'].diff()
    return data.dropna()


def barchart(data, metrics, prefix='', yaxisTitle=''):
    figure = go.Figure(data=[
        go.Bar(
            name=metric, x=data.date, y=data[prefix + metric],
            marker_line_color='rgb(0,0,0)', marker_line_width=1,
            marker_color={'Deaths': 'rgb(200,30,30)', 'Recovered': 'rgb(30,200,30)', 'Confirmed': 'rgb(100,140,240)'}[
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


@app.callback(
    [
        Output('plot_new_metrics', 'figure'),
        Output('plot_cum_metrics', 'figure'),
    ],
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_new_metrics(country, state, metrics):
    data = accumulative_data(country, state)
    new_cases_data = daily_change_data(data)
    new_chart = barchart(new_cases_data, metrics, prefix='New', yaxisTitle='New Cases per Day')
    cum_chart = barchart(data, metrics, prefix='Cum', yaxisTitle='Accumulated Total Cases')
    return new_chart, cum_chart


if __name__ == '__main__':
    app.run_server(debug=True)
