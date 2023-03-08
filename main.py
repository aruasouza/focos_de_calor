import pandas as pd
import requests
import plotly.express as px
import streamlit as st
import io
from datetime import datetime

def get_data():
    url = 'http://queimadas.dgi.inpe.br/api/focos'
    print('Obtendo dados...')
    try:
        req = requests.get(url)
        df = pd.json_normalize(req.json())
        df = df.rename(columns={'properties.longitude':'Longitude','properties.latitude':'Latitude','properties.pais':'País',
        'properties.estado':'Estado','properties.municipio':'Município','properties.risco_fogo':'Risco de Fogo',
        'properties.precipitacao':'Precipitação','properties.numero_dias_sem_chuva':'Dias sem Chuva','properties.data_hora_gmt':'Data',
        'geometry.type':'geometry_type','geometry.coordinates':'geometry_coordinates','properties.satelite':'Satélite'})
        df.to_csv('dados_backup.csv',index = False,sep = ';',decimal = ',')
        time_df = pd.DataFrame({'time':[datetime.now()]})
        time_df.to_csv('time.csv',index = False)
        st.session_state['backup'] = False
    except Exception:
        print('O request falhou')
        df = pd.read_csv('dados_backup.csv',sep = ';',decimal = ',')
        st.session_state['backup'] = True
        st.session_state['time'] = pd.read_csv('time.csv').loc[0,'time']
    return df

def update_figure(df):

    fig = px.density_mapbox(df, lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
        hover_data=["País",'Estado'], zoom=3, height=700)

    fig.update_layout(mapbox_style="stamen-terrain")
    fig.update_layout(transition_duration=500)
    fig.update_layout(margin=dict(l=0,r=0,b=0,t=0))
    fig.update(layout_coloraxis_showscale=False)
    buffer = io.StringIO()
    fig.write_html(buffer)
    st.session_state['html_bytes'] = buffer.getvalue().encode()
    fig.update_layout(height = 500)

    return fig

st.set_page_config(page_title = 'Focos de Calor',layout = 'wide',page_icon = ':earth_americas:')
style = '''
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
.block-container {padding-top:1rem;}
.e1fqkh3o4 {padding-top:1rem;}
</style>
'''

st.markdown(style,unsafe_allow_html=True)
col_title,col_warning = st.columns(2)

col_title.header('Focos de Calor na América do Sul')
col_title.caption('Últimas 24h')

with st.spinner(text='Obtendo dados...'):

    if 'data' not in st.session_state:
        st.session_state['data'] = get_data()
        st.session_state['for_download'] = st.session_state.data.to_csv(index = False, sep = ';',decimal = ',')

figure = update_figure(st.session_state.data)

if st.session_state.backup:
    col_warning.warning(f'A requisição para BDQueimadas falhou. Usando dados coletados em {st.session_state.time}')

st.plotly_chart(figure,use_container_width = True,config = {'displaylogo':False})

cl1,cl2,cl3,cl4,cl5 = st.columns([1,1,2,3,3])
cl1.download_button('Baixar dados',st.session_state.for_download,'focos_de_calor_america_do_sul.csv')
cl2.download_button('Baixar mapa',st.session_state.html_bytes,'mapa.html')
cl4.caption('Dados: https://queimadas.dgi.inpe.br/queimadas/portal')
cl5.caption('Código fonte: https://github.com/aruasouza/focos_de_calor')