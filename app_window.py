import threading
import webview

from dash import Dash, html, page_container
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc


# ========================
# Dash App
# ========================
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = html.Div([
    dmc.MantineProvider(
        page_container
    )
])


# ========================
# Função para rodar o Dash
# ========================
def run_dash():
    app.run(debug=False, port=8050)


# ========================
# Inicialização Desktop
# ========================
if __name__ == "__main__":
    threading.Thread(target=run_dash, daemon=True).start()

    window = webview.create_window(
        "VERSOS Visualizer",
        "http://127.0.0.1:8050",
        resizable=True,
    )

    def maximize(window):
        window.maximize()

    webview.start(maximize, window)