from dash import Dash
import dash
from waitress import serve

app = Dash(__name__, use_pages=True)

app.layout = dash.page_container

server = app.server

if __name__ == '__main__':
	serve(app.server,host="0.0.0.0",port=8000)