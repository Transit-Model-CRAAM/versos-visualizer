import os

from dash import (
    callback,
    register_page,
    set_props,
    html,
    dcc,
    Output,
    Input,
    State,
    Patch,
    no_update,
    callback_context,
    MATCH,
    ALL,
)
import dash_mantine_components as dmc
import plotly.graph_objects as go

from src.functions.data_validation import *
from src.components.cards import generate_card
from src.constants.graph import (
    PLOT_CONFIG,
    generate_validation_fig_properties,
    generate_validation_goes_fig_properties
)
from src.constants.translations import TRANSLATIONS
from urllib.parse import parse_qs


register_page(__name__, path="/validation")


def layout(**kwargs):
    """
    Build the Validation page layout.

    Parameters
    ----------
    **kwargs
        Optional keyword arguments passed by Dash, including language selection.

    Returns
    -------
    dash.html.Div
        Validation page layout container.
    """
    if kwargs.get("lang") and kwargs.get("lang") in TRANSLATIONS:
        lang = kwargs.get("lang")
    else:
        lang = "pt"

    translated = TRANSLATIONS[lang]
    validation_t = translated["validation"]

    logo_path = os.path.join("assets", "versos-logo-v3.png")
    
#    :####:   .####.   ###  ###  ######:    .####.   ###   ##  ########  ###   ##  ########   :####:
#    ######   ######   ###  ###  #######:   ######   ###   ##  ########  ###   ##  ########  :######
#  :##:  .#  :##  ##:  ###::###  ##   :##  :##  ##:  ###:  ##  ##        ###:  ##     ##     ##:  :#
#  ##        ##:  :##  ###  ###  ##    ##  ##:  :##  ####  ##  ##        ####  ##     ##     ##
#  ##.       ##    ##  ## ## ##  ##   :##  ##    ##  ##:#: ##  ##        ##:#: ##     ##     ###:
#  ##        ##    ##  ##:##:##  #######:  ##    ##  ## ## ##  #######   ## ## ##     ##     :#####:
#  ##        ##    ##  ##.##.##  ######:   ##    ##  ## ## ##  #######   ## ## ##     ##      .#####:
#  ##.       ##    ##  ## ## ##  ##        ##    ##  ## :#:##  ##        ## :#:##     ##         :###
#  ##        ##:  :##  ##    ##  ##        ##:  :##  ##  ####  ##        ##  ####     ##           ##
#  :##:  .#  :##  ##:  ##    ##  ##        :##  ##:  ##  :###  ##        ##  :###     ##     #:.  :##
#    ######   ######   ##    ##  ##         ######   ##   ###  ########  ##   ###     ##     #######:
#    :####:   .####.   ##    ##  ##         .####.   ##   ###  ########  ##   ###     ##     .#####:

    top_controls = generate_card(
        html.Div(
            [
                dmc.DateInput(
                    id="validation_date_input",
                    label=translated["components"]["date_input"]["label"],
                    minDate="2011-01-01",
                    maxDate="2020-07-27",
                    className="custom-input validation-date-input",
                ),
                dmc.Button(
                    validation_t["search_data_button"],
                    id="validation_search_data_btn",
                    className="button-style validation-search-btn",
                ),
                dmc.Button(
                    validation_t["load_flares_button"],
                    id="validation_load_flares_btn",
                    className="button-style validation-search-btn",
                ),
            ],
            className="validation-top-controls-content",
        ),
        "first-column-card validation-top-controls-card",
    )

    def _graph_card(title: str, graph_id: str, figure_factory):
        return generate_card(
            html.Div(
                [
                    html.H4(title, className="validation-card-title"),
                    dcc.Graph(
                        id=graph_id,
                        config=PLOT_CONFIG,
                        figure=figure_factory(lang),
                        className="validation-graph",
                    ),
                ],
                className="validation-card-content",
            ),
            "second-column-card validation-graph-card",
        )

    graphs_grid = html.Div(
        [
            _graph_card(
                validation_t["stations"]["palehua"],
                "validation_palehua_graph",
                generate_validation_fig_properties,
            ),
            _graph_card(
                validation_t["stations"]["learmonth"],
                "validation_learmonth_graph",
                generate_validation_fig_properties,
            ),
            _graph_card(
                validation_t["stations"]["sagamore_hill"],
                "validation_sagamore_hill_graph",
                generate_validation_fig_properties,
            ),
            _graph_card(
                validation_t["stations"]["nobeyama"],
                "validation_nobeyama_graph",
                generate_validation_fig_properties,
            ),
            _graph_card(
                validation_t["stations"]["san_vito"],
                "validation_san_vito_graph",
                generate_validation_fig_properties,
            ),
            _graph_card(
                validation_t["goes_xray_data"],
                "validation_goes_xray_graph",
                generate_validation_goes_fig_properties,
            ),
        ],
        className="validation-graphs-grid",
    )
    
    page_notification_container = html.Div(
        [
            dmc.NotificationContainer(id="validation_notification_container")
        ]
    )
    
#  ##          :##:   ###    ###  .####.   ##    ##  ########
#  ##           ##    .##:  :##.  ######   ##    ##  ########
#  ##          ####    ###  ###  :##  ##:  ##    ##     ##
#  ##          ####     ##::##   ##:  :##  ##    ##     ##
#  ##         :#  #:     ####    ##    ##  ##    ##     ##
#  ##          #::#      ####    ##    ##  ##    ##     ##
#  ##         ##  ##     :##:    ##    ##  ##    ##     ##
#  ##         ######      ##     ##    ##  ##    ##     ##
#  ##        .######.     ##     ##:  :##  ##    ##     ##
#  ##        :##  ##:     ##     :##  ##:  ##    ##     ##
#  ########  ###  ###     ##      ######   :######:     ##
#  ########  ##:  :##     ##      .####.    :####:      ##

    return html.Div(
        [
            dmc.LoadingOverlay(
                id="validation_screen_loading_overlay",
                loaderProps={
                    "variant": "custom",
                    "children": dmc.Image(
                        src="/assets/sol.svg",
                        h=200,
                    ),
                },
                overlayProps={"radius": "sm", "blur": 2},
                visible=False,
                zIndex=10,
            ),
            html.Img(src=logo_path, className="validation-bg-logo"),
            html.Div(
                [
                    top_controls,
                ],
                className="validation-top-row",
            ),
            graphs_grid,
            page_notification_container,
            dcc.Location(id="url"),
        ],
        className="validation-page-container",
    )


#    :####:    :##:    ##        ##        ######:     :##:      :####:  ##   ###   :####:
#    ######     ##     ##        ##        #######      ##       ######  ##   ##   :######
#  :##:  .#    ####    ##        ##        ##   :##    ####    :##:  .#  ## :##:   ##:  :#
#  ##          ####    ##        ##        ##    ##    ####    ##        ##.##:    ##
#  ##.        :#  #:   ##        ##        ##   :##   :#  #:   ##.       #####     ###:
#  ##          #::#    ##        ##        #######.    #::#    ##        #####     :#####:
#  ##         ##  ##   ##        ##        #######.   ##  ##   ##        #####:     .#####:
#  ##.        ######   ##        ##        ##   :##   ######   ##.       ##::##        :###
#  ##        .######.  ##        ##        ##    ##  .######.  ##        ##  ##          ##
#  :##:  .#  :##  ##:  ##        ##        ##   :##  :##  ##:  :##:  .#  ##  :##   #:.  :##
#    ######  ###  ###  ########  ########  ########  ###  ###    ######  ##   ##   #######:
#    :####:  ##:  :##  ########  ########  ######    ##:  :##    :####:  ##   :##  .#####:


@callback(
    Output("validation_palehua_graph", "figure"),
    Output("validation_sagamore_hill_graph", "figure"),
    Output("validation_san_vito_graph", "figure"),
    Output("validation_learmonth_graph", "figure"),
    Output("validation_nobeyama_graph", "figure"),
    Output("validation_goes_xray_graph", "figure"),
    Input("validation_search_data_btn", "n_clicks"),
    State("validation_date_input", "value"),
    State("url", "search"),
    running=[
        (Output("validation_search_data_btn", "disabled"), True, False),
        (Output("validation_screen_loading_overlay", "visible"), True, False),
    ],
    prevent_initial_call=True,
)
def update_validation_graphs(n_clicks: int, selected_date: str, search: str) -> tuple:
    """
    Update the validation graphs based on the selected date.

    Parameters
    ----------
    n_clicks : int
    The number of times the search button has been clicked.
    selected_date : str
    The date selected by the user in the date input.

    Returns
    -------
    tuple
    A tuple containing the updated figures for each validation graph.
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
        translated = TRANSLATIONS["pt"]
        
    if not selected_date:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    instruments_data = get_all_data_for_date(selected_date)

    # Unpack the data for each observatory
    palehua_data = instruments_data.get("palehua", {})
    sagamore_hill_data = instruments_data.get("sagamore-hill", {})
    learmonth_data = instruments_data.get("learmonth", {})
    san_vito_data = instruments_data.get("san-vito", {})
    nobeyama_data = instruments_data.get("nobeyama", {})
    goes_data = instruments_data.get("goes", {})

    # Generate figures for each observatory
    palehua_fig = Patch()
    sagamore_hill_fig = Patch()
    san_vito_fig = Patch()
    learmonth_fig = Patch()
    nobeyama_fig = Patch()
    goes_fig = Patch()
    
    hover_template = f"{translated['graphs']['point']} " + "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"

    if palehua_data.get("timestamps") is not None and palehua_data.get("freq_intensities") is not None:
        palehua_fig["data"] = [
            go.Scatter(
                y=intensity, 
                x=palehua_data["timestamps"],
                mode="lines",
                name=f"{frequency} GHz",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
            for (intensity, frequency) in zip(
                palehua_data["freq_intensities"].T,
                palehua_data["frequency_list"],
            )
        ]
        palehua_fig["layout"]["annotations"] = []  # Remove any previous annotations
    else:
        # If there's no data, clear the graph and show a "No data found" message
        palehua_fig["data"] = []
        palehua_fig["layout"]["annotations"] = [dict(
            text=translated['graphs']['no_data_found'],
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=20)
        )]

    if sagamore_hill_data.get("timestamps") is not None and sagamore_hill_data.get("freq_intensities") is not None:
        sagamore_hill_fig["data"] = [
            go.Scatter(
                y=intensity,
                x=sagamore_hill_data["timestamps"],
                mode="lines",
                name=f"{frequency} GHz",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
            for (intensity, frequency) in zip(
                sagamore_hill_data.get("freq_intensities", np.array([])).T,
                sagamore_hill_data.get("frequency_list", []),
            )
        ]
        sagamore_hill_fig["layout"]["annotations"] = []  # Remove any previous annotations
    else:
        sagamore_hill_fig["data"] = []
        sagamore_hill_fig["layout"]["annotations"] = [dict(
            text=translated['graphs']['no_data_found'],
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=20)
        )]

    if learmonth_data.get("timestamps") is not None and learmonth_data.get("freq_intensities") is not None:
        learmonth_fig["data"] = [
            go.Scatter(
                y=intensity,
                x=learmonth_data.get("timestamps", []),
                mode="lines",
                name=f"{frequency} GHz",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
            for (intensity, frequency) in zip(
                learmonth_data.get("freq_intensities", np.array([])).T,
                learmonth_data.get("frequency_list", []),
            )
        ]
        learmonth_fig["layout"]["annotations"] = []  # Remove any previous annotations
    else:
        learmonth_fig["data"] = []
        learmonth_fig["layout"]["annotations"] = [dict(
            text=translated['graphs']['no_data_found'],
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=20)
        )]

    if san_vito_data.get("timestamps") is not None and san_vito_data.get("freq_intensities") is not None:
        san_vito_fig["data"] = [
            go.Scatter(
                y=intensity,
                x=san_vito_data.get("timestamps", []),
                mode="lines",
                name=f"{frequency} GHz",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
            for (intensity, frequency) in zip(
                san_vito_data.get("freq_intensities", np.array([])).T,
                san_vito_data.get("frequency_list", []),
            )
        ]
        san_vito_fig["layout"]["annotations"] = []
    else:
        san_vito_fig["data"] = []
        san_vito_fig["layout"]["annotations"] = [dict(
            text=translated['graphs']['no_data_found'],
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=20)
        )]

    if nobeyama_data.get("timestamps") is not None and nobeyama_data.get("freq_intensities") is not None:
        nobeyama_fig["data"] = [
            go.Scatter(
                y=intensity,
                x=nobeyama_data.get("timestamps", []),
                mode="lines",
                name=f"{frequency:.2f} GHz",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
            for (intensity, frequency) in zip(
                nobeyama_data.get("freq_intensities", np.array([])).T,
                nobeyama_data.get("frequency_list", []),
            )
        ]
        nobeyama_fig["layout"]["annotations"] = []  # Remove any previous annotations
    else:
        nobeyama_fig["data"] = []
        nobeyama_fig["layout"]["annotations"] = [dict(
            text=translated['graphs']['no_data_found'],
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=20)
        )]

    # Pega o DataFrame de dentro do dicionário
    df_goes = goes_data.get("data")
    ts_goes = goes_data.get("timestamps", [])

    if df_goes is not None and not df_goes.empty:
        hover_template = f"{translated['graphs']['point']} " + "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.2e}<extra></extra>"
        goes_fig["data"] = [
            # Canal XRS-B (O mais importante para classificação)
            go.Scatter(
                x=ts_goes,
                y=df_goes["xrsb_flux"], 
                mode="lines",
                name="GOES XRS-B (0.1-0.8nm)",
                line=dict(width=2, color="red"),
                hovertemplate=hover_template,
            ),
            # Canal XRS-A (Opcional, mas bom para comparação)
            go.Scatter(
                x=ts_goes,
                y=df_goes["xrsa_flux"],
                mode="lines",
                name="GOES XRS-A (0.05-0.4nm)",
                line=dict(width=1, color="blue"),
                opacity=0.5,
                hovertemplate=hover_template,
            )
        ]
        goes_fig["layout"]["annotations"] = [
            {"x": 1, "y": -8.5, "xref": "paper", "yref": "y", "text": "A", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -7.5, "xref": "paper", "yref": "y", "text": "B", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -6.5, "xref": "paper", "yref": "y", "text": "C", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -5.5, "xref": "paper", "yref": "y", "text": "M", "showarrow": False, "font": {"color": "orange", "size": 14}},
            {"x": 1, "y": -4.5, "xref": "paper", "yref": "y", "text": "X", "showarrow": False, "font": {"color": "red", "size": 14}},
        ]
    else:
        goes_fig["data"] = []
        goes_fig["layout"]["annotations"] = [
            dict(
                text=translated['graphs']['no_data_found'],
                xref="paper", yref="paper",
                showarrow=False, font=dict(size=20)
            ),
            {"x": 1, "y": -8.5, "xref": "paper", "yref": "y", "text": "A", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -7.5, "xref": "paper", "yref": "y", "text": "B", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -6.5, "xref": "paper", "yref": "y", "text": "C", "showarrow": False, "font": {"color": "gray"}},
            {"x": 1, "y": -5.5, "xref": "paper", "yref": "y", "text": "M", "showarrow": False, "font": {"color": "orange", "size": 14}},
            {"x": 1, "y": -4.5, "xref": "paper", "yref": "y", "text": "X", "showarrow": False, "font": {"color": "red", "size": 14}},
        ]

    return (
        palehua_fig,
        sagamore_hill_fig,
        san_vito_fig,
        learmonth_fig,
        nobeyama_fig,
        goes_fig,
    )


@callback(
    Output("validation_palehua_graph", "figure", allow_duplicate=True),
    Output("validation_sagamore_hill_graph", "figure", allow_duplicate=True),
    Output("validation_san_vito_graph", "figure", allow_duplicate=True),
    Output("validation_learmonth_graph", "figure", allow_duplicate=True),
    Output("validation_nobeyama_graph", "figure", allow_duplicate=True),
    Output("validation_goes_xray_graph", "figure", allow_duplicate=True),
    Input("validation_load_flares_btn", "n_clicks"),
    prevent_initial_call=True,
)
def validation_load_flares(n_clicks: int) -> tuple:
    """
    Load flare annotations onto the validation graphs.

    Parameters
    ----------
    n_clicks : int
        The number of times the "Load Flares" button has been clicked.

    Returns
    -------
    tuple
        A tuple containing the updated figures for each validation graph with flare annotations.
    """
    flare_data = load_event_times_from_json()

    patched_figure = Patch()

    shapes = [
        {
            "type": "rect",
            "xref": "x",
            "yref": "paper",
            "x0": data["start"],
            "x1": data["end"],
            "y0": 0,
            "y1": 1,
            "fillcolor": "#ffcb48",
            "opacity": 0.6,
            "line": {"width": 0},
        }
        for data in flare_data
    ]

    patched_figure["layout"]["shapes"] = shapes

    return (
        patched_figure,
        patched_figure,
        patched_figure,
        patched_figure,
        patched_figure,
        patched_figure,
    )