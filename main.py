from dash import Dash
import dash

app = Dash(__name__, use_pages=True)

app.layout = dash.page_container

server = app.server

if __name__ == '__main__':
	app.run_server()