from dash import html, Output, Input, State, Patch
import dash_bootstrap_components as dbc

def generate_card(children, className=""):
    return html.Div(
        children=children,
        className=f"content-card {className}"
    )