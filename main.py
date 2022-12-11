import pandas as pd
import requests
import plotly.express as px
import streamlit as st
import io

def reduce_capilarity(data):
    return pd.Timestamp(f'{data.year}-{data.month}-{data.day} {data.hour}:00:00')

def hora(num):
    value = str(num)
    if len(value) == 1:
        value = '0' + value
    return value + 'h'

def get_data():
    url = 'http://queimadas.dgi.inpe.br/api/focos'
    print('Obtendo dados...')
    try:
        req = requests.get(url)
        df = pd.json_normalize(req.json())
        df = df.rename(columns={'properties.longitude':'Longitude','properties.latitude':'Latitude','properties.pais':'País',
        'properties.estado':'Estado','properties.municipio':'Município','properties.risco_fogo':'Risco de Fogo',
        'properties.precipitacao':'Precipitação','properties.numero_dias_sem_chuva':'Dias sem Chuva','properties.data_hora_gmt':'Data'})
        df['Risco de Fogo'] = df['Risco de Fogo'].fillna('?')
        df['Precipitação'] = df['Precipitação'].fillna('?')
        df['Dias sem Chuva'] = df['Dias sem Chuva'].fillna('?')
    except:
        print('O request falhou')
        df = pd.read_csv('dados_backup.csv',sep = ';',decimal = ',')
        st.session_state['backup'] = True
    return df

def update_figure(df):

    fig = px.density_mapbox(df, lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
        hover_data=["País",'Estado','Precipitação','Dias sem Chuva','Risco de Fogo'], zoom=3, height=700)

    fig.update_layout(mapbox_style="stamen-terrain")
    fig.update_layout(transition_duration=500)
    fig.update_layout(margin=dict(l=0,r=0,b=0,t=0))
    fig.update(layout_coloraxis_showscale=False)
    buffer = io.StringIO()
    fig.write_html(buffer)
    st.session_state['html_bytes'] = buffer.getvalue().encode()
    fig.update_layout(height = 550)

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
st.header('Focos de Calor na América do Sul')

with st.spinner(text='Obtendo dados...'):

    if 'data' not in st.session_state:
        st.session_state['backup'] = False
        st.session_state['data'] = get_data()
        st.session_state['for_download'] = st.session_state.data.to_csv(index = False, sep = ';',decimal = ',')

figure = update_figure(st.session_state.data)

st.plotly_chart(figure,use_container_width = True,config = {'displaylogo':False})
if st.session_state.backup:
    st.warning('A requisição para BDQueimadas falhou. Usando dados coletados em 11/12/2022 às 09:13.')

with st.sidebar:
    st.write('Aplicação produzida como trabalho final na disciplina de Conservação de Recursos Naturais')
    st.write('Alunos:')
    st.write('Aruã Viggiano Souza')
    st.download_button('Baixar dados',st.session_state.for_download,'focos_de_calor_america_do_sul.csv')
    st.download_button('Baixar mapa',st.session_state.html_bytes,'mapa.html')