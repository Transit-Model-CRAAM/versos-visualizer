from dash import Dash, html, page_container
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = html.Div([dmc.MantineProvider(page_container)])

if __name__ == "__main__":
    app.run(debug=True)