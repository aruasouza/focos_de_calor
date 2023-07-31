import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime
import io
from base64 import b64encode
from dash.dependencies import Output, Input, State
from dash import callback_context
import urllib

dash.register_page(__name__, path='/')

font_color = 'rgb(100,100,100)'

def get_data():
    url = 'http://queimadas.dgi.inpe.br/api/focos'
    with open('time','r') as f:
        time = f.read().split('.')[0]
    t = datetime.strptime(time,'%Y-%m-%d %H:%M:%S')
    delta = datetime.now() - t
    if (delta.seconds > 3600) or (delta.days > 0):
        try:
            print('Obtendo dados do BDQueimadas...')
            req = requests.get(url)
            df = pd.json_normalize(req.json())
            df = df.rename(columns={'properties.longitude':'Longitude','properties.latitude':'Latitude','properties.pais':'País',
            'properties.estado':'Estado','properties.municipio':'Município','properties.risco_fogo':'Risco de Fogo',
            'properties.precipitacao':'Precipitação','properties.numero_dias_sem_chuva':'Dias sem Chuva','properties.data_hora_gmt':'Datetime',
            'geometry.type':'geometry_type','geometry.coordinates':'geometry_coordinates','properties.satelite':'Satélite'})
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df['Datetime'] = df['Datetime'].dt.tz_convert('America/Sao_Paulo')
            df['Data'] = df['Datetime'].apply(datetime_to_data)
            df['Hora'] = df['Datetime'].apply(datetime_to_hora)
            df.to_csv('dados_backup.csv',index = False,sep = ';',decimal = ',')
            time = datetime.now()
            with open('time','w') as f:
                f.write(str(time))
            backup = False
            time = 0
            print('Success')
        except Exception:
            print('O request falhou')
            df = pd.read_csv('dados_backup.csv',sep = ';',decimal = ',')
            backup = True
            with open('time','r') as f:
                time = f.read().split('.')[0]
    else:
        print('Obtendo dados do disco...')
        df = pd.read_csv('dados_backup.csv',sep = ';',decimal = ',')
        backup = False
        time = 0
    return df,backup,time

def datetime_to_data(date):
    ano = str(date.year)
    mes = str(date.month)
    mes = mes if len(mes) == 2 else '0' + mes
    dia = str(date.day)
    dia = dia if len(dia) == 2 else '0' + dia
    return dia + '/' + mes + '/' + ano

def datetime_to_hora(date):
    hora = str(date.hour)
    hora = hora if len(hora) == 2 else '0' + hora
    minuto = str(date.minute)
    minuto = minuto if len(minuto) == 2 else '0' + minuto
    sec = str(date.second)
    sec = sec if len(sec) == 2 else '0' + sec
    return hora + ':' + minuto + ':' + sec

def inicial_figure():
    fig = px.density_mapbox(pd.DataFrame({'Município':[],'Latitude':[],'Longitude':[],'País':[],'Estado':[]}),
                            lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
                            hover_data=["País",'Estado'], zoom=3,color_continuous_scale = 'Hot')
    fig.update_layout(mapbox_style='stamen-terrain',transition_duration=500,margin=dict(l=0,r=0,b=0,t=30),
                      title={'text': 'Obtendo dados, aguarde...','xanchor': 'center','yanchor': 'top','y':0.99,'x':0.5})
    return fig

@callback(Output('data', 'data'),Output('mapa','figure'), Input('modo_escuro', 'value'), State('data', 'data'),State('mapa','figure'))
def update_data(value, data, fig):
    if not data or not callback_context.triggered:
        data,backup,time = get_data()
        fig = px.density_mapbox(data, lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
        hover_data=["País",'Estado','Data','Hora'], zoom=3,color_continuous_scale = 'Hot')
        if not backup:
            fig.update_layout(mapbox_style = 'stamen-terrain',transition_duration=500,margin=dict(l=0,r=0,b=0,t=0))
        else:
            fig.update_layout(mapbox_style = 'stamen-terrain',transition_duration=500,margin=dict(l=0,r=0,b=0,t=25),
                              title={'text': f'A conexão com BDQueimadas falhou. Usando dados obtidos em {time}',
                                     'xanchor': 'center','yanchor': 'top','y':0.99,'x':0.5},font = {'size':10,'color':'red'})
        fig.update(layout_coloraxis_showscale=False)
        data = data.to_json(orient='split')
        return data,fig
    fig = go.Figure(fig)
    if value == ['Modo Escuro']:
        fig.update_layout(mapbox_style="carto-darkmatter")
    else:
        fig.update_layout(mapbox_style = 'stamen-terrain')
    return data,fig

@callback(Output('baixar_mapa','href'),Input('mapa','figure'))
def create_html(figure):
    fig = go.Figure(figure)
    buffer = io.StringIO()
    fig.write_html(buffer)
    html_bytes = buffer.getvalue().encode()
    encoded = b64encode(html_bytes).decode()
    return "data:text/html;base64," + encoded

@callback(Output('baixar_dados','href'),Input('data','data'))
def create_csv(data):
    df = pd.read_json(data, orient='split')
    csv = df.to_csv(index = False)
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv)

@callback(Output('info','style'),Output('fade','style'),Output('sobre','disabled'),Input('sobre','n_clicks'),Input('closeInfo','n_clicks'))
def show_info(open,close):
    if open > close:
        return {'display':'block'},{'display':'block'},True
    return {'display': 'none'},{'display': 'none'},False

@callback(Output('dashboard','style'),Output('fade2','style'),Output('dashButton','disabled'),Input('dashButton','n_clicks'),Input('closeDash','n_clicks'))
def show_dash(open,close):
    if open > close:
        return {'display':'block'},{'display':'block'},True
    return {'display': 'none'},{'display': 'none'},False

@callback(Output('bargraph','figure'),Input('data','data'))
def build_graphs(data):
    df = pd.read_json(data, orient='split')
    fig = make_subplots(rows=2, cols=2,subplot_titles=("Focos por País", "Focos por Satélite","Focos por Hora"),specs=[[{}, {}],[{"colspan": 2}, None]])
    df['Focos'] = 1
    group1 = df[['País','Focos']].groupby('País').count().sort_values('Focos',ascending=False)
    if len(group1) > 6:
        group1 = pd.concat([group1.iloc[:5],pd.DataFrame({'Focos':[group1.iloc[5:]['Focos'].sum()]},index = ['Outros'])])
    fig.add_trace(go.Bar(x = group1.index,y = group1['Focos'],text=group1['Focos'],textposition='auto'),row = 1,col = 1)
    group2 = df[['Satélite','Focos']].groupby('Satélite').count().sort_values('Focos',ascending=False)
    if len(group2) > 6:
        group2 = pd.concat([group2.iloc[:5],pd.DataFrame({'Focos':[group2.iloc[5:]['Focos'].sum()]},index = ['Outros'])])
    fig.add_trace(go.Bar(x = group2.index,y = group2['Focos'],text=group2['Focos'],textposition='auto'),row = 1,col = 2)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df['hora_do_dia'] = df['Datetime'].dt.hour
    df['dia'] = df['Datetime'].dt.day
    df['mes'] = df['Datetime'].dt.month
    df['ano'] = df['Datetime'].dt.year
    df['new_datetime'] = df.apply(lambda x: datetime(x['ano'],x['mes'],x['dia'],x['hora_do_dia']),axis = 1)
    group3 = df[['new_datetime','Focos']].groupby('new_datetime').count()
    fig.add_trace(go.Scatter(x = group3.index,y = group3['Focos']),row = 2,col = 1)
    fig.update_layout(showlegend=False,margin=dict(l=0, r=0, t=30, b=0),height = 610,template = 'seaborn')
    fig.update_yaxes(showticklabels=False)
    return fig

layout = html.Div([
    dcc.Store(id = 'data'),
    html.H1('Focos de Calor na América do Sul',
            style = {'font-family':'helvetica','background-color':'white','border-radius':'5px',
                        'padding':'10px','color':font_color,'margin':'10px','float':'left','font-size':'23px'},id = 'title'),
    html.Div([
        html.A(html.Button('Baixar Dados',className = 'menuButton'),id = 'baixar_dados',download = 'focos_de_calor.csv'),html.Br(),
        html.A(html.Button('Baixar Mapa',className = 'menuButton'),id = 'baixar_mapa',download = 'focos_de_calor.html'),html.Br(),
        html.A(html.Button('Dashboard',className = 'menuButton',id = 'dashButton',n_clicks = 0)),html.Br(),
        html.A(html.Button('Sobre',id = 'sobre',className = 'menuButton',n_clicks = 0))],
        style = {'position': 'fixed', 'top': '0', 'left': '0','margin-top':'75px','margin-left':'10px'}),
    dcc.Graph(
        id='mapa',
        figure = inicial_figure(),
        style = {'position': 'fixed', 'top': '0', 'left': '0','height': '100vh', 'width': '100vw', 'z-index': '-1'}
    ),
    html.Div(id = 'fade',className = 'fade'),
    html.Div([
        html.Button('X',id = 'closeInfo',n_clicks = 0,className = 'close'),
        html.Div([
            html.H2('Sobre o projeto'),
            html.P('Dados de satélite das últimas 24h.'),
            html.P(['Fonte dos dados: ',html.A('BDQueimadas',href = 'https://queimadas.dgi.inpe.br/queimadas/portal')]),
            html.P(['Criado por: ',html.A('Aruã Viggiano Souza',href = 'https://www.linkedin.com/in/aru%C3%A3-viggiano-souza/')]),
            html.P(['Código fonte: ',html.A('Github',href = 'https://github.com/aruasouza/focos-de-calor-dash')])
        ],className = 'blocoTexto')],id = 'info'),
    html.Div(id = 'fade2',className = 'fade'),
    html.Div([
        html.Button('X',id = 'closeDash',n_clicks = 0,className = 'close'),
        html.Div([
            html.H2('Dashboard'),
            dcc.Graph(id = 'bargraph'),
        ],className = 'blocoDash')],id = 'dashboard'),
    dcc.Checklist(id = 'modo_escuro',options = ['Modo Escuro'],style = {'position': 'fixed', 'top':'93%','left':'1%','color':'rgb(100,100,100)',
                                           'background-color':'white','padding':'5px','border-radius':'10px','font-family':'helvetica'})
])