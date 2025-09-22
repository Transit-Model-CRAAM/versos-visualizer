import os
import base64

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
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from scipy.signal import find_peaks, peak_widths
from urllib.parse import parse_qs

from src.components.cards import generate_card
from src.functions.data_treatment import *
from src.constants.graph import *
from src.constants.translations import TRANSLATIONS

register_page(__name__, path="/")

def layout(**kwargs):
    with open("assets/sun_spinning.gif", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    if kwargs.get("lang") and kwargs.get("lang") == "en":
        lang = "en"
    else:
        lang = "pt"
    translated = TRANSLATIONS[lang]

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

    logo_path = os.path.join("assets", "versos-logo-v3.png")

    logo_card = html.Div(
        [
            html.Img(src=logo_path, className="logo-style"),
        ],
        className="logo-card-content"
    )

    timepicker_card = html.Div(
        [
            dmc.DateInput(
                id="home_date_input",
                label=translated["components"]["date_input"]["label"],
                # description=translated["components"]["date_input"]["description"],
                minDate="2012-01-24",
                maxDate="2012-01-30",
                className="custom-input",
            ),
            dmc.Select(
                id="home_data_select",
                label=translated["components"]["data_select"],
                value="4",
                data=[
                    {"value": "4", "label": "TBL_45"},
                    {"value": "5", "label": "TBR_45"},
                    {"value": "6", "label": "TBL_90"},
                    {"value": "7", "label": "TBR_90"},
                ]
            ), 
            dmc.Button(
                translated["components"]["load_button"],
                id="home_load_data_btn",
                disabled=True,
                className="button-style load-data-btn"
            )
        ],
        className="same-line timepicker-card-content first-column-card"
    )

    data_graph_card = html.Div(
        [
            html.Div(
                [
                    dmc.LoadingOverlay(
                        id="home_data_graph_loading_overlay",
                        loaderProps={
                            "variant": "custom",
                            "children": dmc.Image(
                                h=100,
                                radius="md",
                                src=f"data:image/gif;base64,{encoded}",
                            ),
                        },
                        overlayProps={"radius": "sm", "blur": 2},
                        visible=False,
                        zIndex=10,
                    ),
                    dcc.Graph(
                        id="home_data_graph",
                        config=PLOT_CONFIG,
                        figure=generate_fig_properties(lang),
                    ),
                ],
                className="home-data-graph"
            ),
            html.Div(
                [
                    dmc.NumberInput(
                        label=translated["components"]["smooth_window"],
                        id="home_smooth_window_input",
                        value=125,
                        min=1,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["iteration_quantity"],
                        id="home_n_apply_smooth_input",
                        value=2,
                        min=0,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.Button(
                        translated["components"]["apply_dtw_button"],
                        id="home_apply_dtw_btn",
                        disabled=True,
                        className="button-style load-data-btn"
                    )
                ],
                className="same-line home-data-graph-inputs"
            )
        ],
        className="data-graph-card first-column-card"
    )

    background_graph_card = html.Div(
        [
            dmc.LoadingOverlay(
                id="home_background_graph_loading_overlay",
                loaderProps={
                    "variant": "custom",
                    "children": dmc.Image(
                        h=100,
                        radius="md",
                        src=f"data:image/gif;base64,{encoded}",
                    ),
                },
                overlayProps={"radius": "sm", "blur": 2},
                visible=False,
                zIndex=10,
            ),
            dcc.Graph(
                id="home_background_graph",
                config=PLOT_CONFIG,
                figure=generate_background_fig_properties(lang),
            )
        ],
        className="home-background-graph second-column-card"
    )

    inputs_card = html.Div(
        [
            html.Div(
                [
                    dmc.NumberInput(
                        label=translated["components"]["std_input"],
                        id="home_diff_std_input",
                        value=2,
                        min=1.5,
                        max=3.5,
                        disabled=True,
                        debounce=True,
                        decimalScale=2,
                        step=0.1,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["merge_gap"],
                        id="home_merge_gap_input",
                        value=250,
                        min=1,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["relative_height"],
                        id="home_relative_height_input",
                        value=0.5,
                        min=0,
                        disabled=True,
                        debounce=True,
                        decimalScale=2,
                        step=0.01,
                    ),
                ],
                className="same-line home-inputs-blocks"
            ),
            html.Div(
                [
                    dmc.NumberInput(
                        label=translated["components"]["min_curves"],
                        id="home_min_curves_input",
                        value=5,
                        min=1,
                        max=6,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.Button(
                        translated["components"]["obtain_results_button"],
                        id="home_get_results_btn",
                        disabled=True,
                        className="button-style get-results-btn"
                    )
                ],
                className="same-line home-inputs-blocks"
            ),
        ],
        className="home-inputs third-column-card"
    )

    results_graph_card = html.Div(
        [
            html.Div(
                [
                    dmc.Tabs(
                        [
                            dmc.TabsList(
                                [
                                    dmc.TabsTab(translated["components"]["results_tab"]["results"], value="result"),
                                    dmc.TabsTab(translated["components"]["results_tab"]["background_curve"], value="background"),
                                ]
                            ),
                            dmc.TabsPanel(
                                [
                                    html.Div(
                                        [
                                            dmc.LoadingOverlay(
                                                id="home_result_graph_loading_overlay",
                                                loaderProps={
                                                    "variant": "custom",
                                                    "children": dmc.Image(
                                                        h=100,
                                                        radius="md",
                                                        src=f"data:image/gif;base64,{encoded}",
                                                    ),
                                                },
                                                overlayProps={"radius": "sm", "blur": 2},
                                                visible=False,
                                                zIndex=10,
                                            ),
                                            dcc.Graph(
                                                id="home_results_graph",
                                                config=PLOT_CONFIG,
                                                figure=generate_fig_properties(lang),
                                            )
                                        ],
                                        className="home-results-graph"
                                    ),
                                ],
                                value="result",
                                className="home-results-graph",
                            ),
                            dmc.TabsPanel(
                                [
                                    html.Div(
                                        [
                                            dmc.LoadingOverlay(
                                                id="home_result_background_graph_loading_overlay",
                                                loaderProps={
                                                    "variant": "custom",
                                                    "children": dmc.Image(
                                                        h=100,
                                                        radius="md",
                                                        src=f"data:image/gif;base64,{encoded}",
                                                    ),
                                                },
                                                overlayProps={"radius": "sm", "blur": 2},
                                                visible=False,
                                                zIndex=10,
                                            ),
                                            dcc.Graph(
                                                id="home_results_background_graph",
                                                config=PLOT_CONFIG,
                                                figure=generate_fig_properties(lang),
                                            )
                                        ],
                                        className="home-results-graph"
                                    ),
                                ],
                                value="background",
                                className="home-results-graph",
                            ),
                        ],
                        value="result",
                        className="home-results-graph",
                    ),
                ],
                className="results-graph-contents",
            ),
            html.Div(
                [
                    dmc.LoadingOverlay(
                        id="home_result_log_loading_overlay",
                        loaderProps={
                            "variant": "custom",
                            "children": dmc.Image(
                                h=100,
                                radius="md",
                                src=f"data:image/gif;base64,{encoded}",
                            ),
                        },
                        overlayProps={"radius": "sm", "blur": 2},
                        visible=False,
                        zIndex=10,
                        style={"margin-top": "10px"},
                    ),
                    dbc.ListGroup(
                        [],
                        id="home_results_log",
                        className="home-results-log"
                    )
                ],
                className="home-results-log-overlay"
            ),
            html.Div(
                [
                    dmc.Select(
                        id="home_download_extension_select",
                        label=translated["components"]["download_select"]["label"],
                        value="pdf",
                        data=[
                            {"value": "pdf", "label": translated["components"]["download_select"]["values"]["pdf"]},
                            {"value": "csv", "label": translated["components"]["download_select"]["values"]["csv"]},
                        ],
                        comboboxProps={"position": "top", "middlewares": {"flip": False, "shift": False}},
                        className="home-download-select"
                    ),
                    dmc.Button(
                        translated["components"]["download_button"],
                        id="home_download_button",
                        className="button-style load-data-btn",
                        disabled=True,
                    ),
                ],
                className="same-line download-content",
            )
        ],
        className="data-results-card third-column-card"
    )

    page_store = html.Div(
        [
            dcc.Store(id="home_graph_raw_data"),
            dcc.Store(id="home_dtw_result_data"),
            dcc.Store(id="home_peaks_intervals"),
            dcc.Store(id="home_events_data"),
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
            html.Div(
                [
                    generate_card(logo_card, "logo-card"),
                    generate_card(timepicker_card, "timepicker-card"),
                    generate_card(data_graph_card, "data-graph-card"),
                ],
                className="home-page-card-width"
            ),
            html.Div(
                [
                    generate_card(background_graph_card, "background-graph-card")
                ],
                className="home-page-card-width"
            ),
            html.Div(
                [
                    generate_card(inputs_card, "inputs-card"),
                    generate_card(results_graph_card, "results-card"),
                ],
                className="home-page-card-width"
            ),
            page_store,
            dcc.Location(id="url"),
        ],
        className="same-line page-container"
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


# =============================== DATE CARD CALLBACK ======================================

@callback(
    Output("home_load_data_btn", "disabled"),
    Input("home_date_input", "value"),
    prevent_initial_call=True,
)
def home_enable_load_data_btn(date: str) -> bool:
    """
    Enable the click of the `Load Data` button when a date is currently selected.

    Parameters
    ----------
    date : str or None
        The date of the curve to be analyzed (YYYY-MM-DD format).
        If None, that means no date was selected.

    Returns
    -------
    bool
        False if a date is selected, enabling the button;
        True if a date wasn't selected, disabling the button.
    """
    if date is not None:
        return False

    return True

def to_list(arr):
    return np.ascontiguousarray(arr).tolist()
def fits_table_to_list_of_lists(fits_table):
    return [list(row) for row in fits_table]

@callback(
    Output("home_data_graph", "figure"),
    Output("home_background_graph", "figure"),
    Output("home_results_graph", "figure"),
    Output("home_results_background_graph", "figure"),
    Output("home_graph_raw_data", "data"),
    Output("home_results_log", "children"),
    Input("home_load_data_btn", "n_clicks"),
    State("home_data_select", "value"),
    State("home_smooth_window_input", "value"),
    State("home_n_apply_smooth_input", "value"),
    State("home_date_input", "value"),
    State("url", "search"),
    running=[
        (Output("home_data_graph_loading_overlay", "visible"), True, False),
        (Output("home_background_graph_loading_overlay", "visible"), True, False),
        (Output("home_result_graph_loading_overlay", "visible"), True, False),
        (Output("home_result_background_graph_loading_overlay", "visible"), True, False),
        (Output("home_result_log_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, True),
        (Output("home_min_curves_input", "disabled"), True, True),
        (Output("home_merge_gap_input", "disabled"), True, True),
        (Output("home_relative_height_input", "disabled"), True, True),
        (Output("home_get_results_btn", "disabled"), True, True),
        (Output("home_download_button", "disabled"), True, True),
    ],
    prevent_initial_call=True,
)
def home_load_data(
    nc1: int,
    data_select: int,
    smooth_window: int,
    n_apply_smooth: int,
    date: str,
    search: str,
) -> tuple[Patch, dict, dict, dict, dict, list]:
    """
    Function responsible for loading the data, plotting into the `home_data_graph` and storing
    the raw data of all curves inside the store `home_graph_raw_data`.

    Parameters
    ----------
    nc1 : int
        Input for when load data button is clicked.

    data_select : int
        The position of the curve to be loaded in the fits file. Possible values are::

            4 -> "TBL_45"
            5 -> "TBR_45"
            6 -> "TBL_90"
            7 -> "TBR_90"

    smooth_window : int
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    date: str
        The date of the curve to be analyzed (YYYY-MM-DD format).

    search : str
        The extra parameters of the url.

    Returns
    -------
    Patch
        A patched figure to update the curves of the graph with the treated curves.

    dict
        BACKGROUND_FIG_PROPERTIES to reset the background graph.

    dict
        FIG_PROPERTIES to reset the results graph.

    dict
        FIG_PROPERTIES to reset the results background graph.

    dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list of float
                        X-axis data of the target curve.
                    "table": Fits table
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list of list of float
                        X-axis data of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }

    list
        Empty list to reset the results log.
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    if lang == "en":
        translated = TRANSLATIONS["en"]
    else:
        lang = "pt"
        translated = TRANSLATIONS["pt"]
        
    # TODO: This is hardcoded for now. Deal with it in the future
    all_files = [
        os.path.join("data", "D24.fits"),
        os.path.join("data", "D25.fits"),
        os.path.join("data", "D26.fits"),
        os.path.join("data", "D27.fits"),
        os.path.join("data", "D28.fits"),
        os.path.join("data", "D29.fits"),
        os.path.join("data", "D30.fits"),
    ]

    target_file_to_load = os.path.join("data", f"D{date[-2:]}.fits")

    curve_data_list = []
    curve_days = []

    for file in all_files:
        data, full_table, day = load_fits_data(file, int(data_select))

        if file == target_file_to_load:
            target_data = data
            target_full_table = full_table
            target_day = day
            continue

        curve_data_list.append(data)
        curve_days.append(day)

    loaded_data = {
        "target": {
            "data": to_list(target_data),
            "table": fits_table_to_list_of_lists(target_full_table),
            "day": target_day
        },
        "curves": {
            "data_list": [to_list(curva) for curva in curve_data_list],
            "days": curve_days,
        }
    }

    # ======== Pré-processar e interpolar todas ========

    # Pré-processar todas as curvas e target
    curvas_norm = [preprocess_curve(curva, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth) for curva in curve_data_list]
    target_data_norm = preprocess_curve(target_data, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth)

    # Definir tamanho alvo para interpolação (pode ser o da curva target)
    target_len = len(target_data_norm)

    # Interpolar todas para o mesmo tamanho
    curvas_interp = [interpolate_curve(curva, target_len) for curva in curvas_norm]
    target_data_interp = interpolate_curve(target_data_norm, target_len)

    # Calcular mínimo global entre todas as curvas interpoladas e target
    todos_valores = np.concatenate(curvas_interp + [target_data_interp])
    min_global = np.min(todos_valores)

    # Ajustar curvas para que mínimo global seja 0
    curvas_alinhadas = [curva - min_global for curva in curvas_interp]
    target_alinhada = target_data_interp - min_global

    patched_figure = Patch()

    patched_figure["data"] = []

    hover_template = f"{translated['graphs']['point']} " + "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"

    for idx, curva in enumerate(curvas_alinhadas):
        patched_figure["data"].append(
            go.Scatter(
                y=curva,
                mode='lines',
                name=f"{curve_days[idx]}",
                line=dict(width=1.5),
                opacity=0.6,
                hovertemplate=hover_template,
            )
        )

    patched_figure["data"].append(
        go.Scatter(
            y=target_alinhada,
            mode='lines',
            name=f"[TARGET] {target_day}",
            line=dict(width=2.5),
            opacity=1,
            hovertemplate=hover_template,
        )
    )

    return patched_figure, generate_background_fig_properties(lang), generate_fig_properties(lang), generate_fig_properties(lang), loaded_data, []

@callback(
    Output("home_data_graph", "figure", allow_duplicate=True),
    Input("home_smooth_window_input", "value"),
    Input("home_n_apply_smooth_input", "value"),
    State("home_graph_raw_data", "data"),
    running=[
        (Output("home_data_graph_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False)
    ],
    prevent_initial_call=True,
)
def home_update_data(
    smooth_window: int,
    n_apply_smooth: int,
    loaded_data: dict
) -> Patch:
    """
    Function responsible for updating the graph data given new `smooth_window` or `n_apply_smooth`,
    plotting into the `home_data_graph`.

    Parameters
    ----------
    smooth_window : int
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    loaded_data: dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list of float
                        X-axis data of the target curve.
                    "table": Fits table
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list of list of float
                        X-axis data of the curves to be compared.
                    "days": list of str
                        The day of each curve.
                }
            }

    Returns
    -------
    Patch
        A patched figure to update the curves of the graph with the treated curves.
    """
    target_data = loaded_data["target"]["data"]

    curve_data_list = loaded_data["curves"]["data_list"]

    # ======== Pré-processar e interpolar todas ========

    # Pré-processar todas as curvas e target
    curvas_norm = [preprocess_curve(curva, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth) for curva in curve_data_list]
    target_data_norm = preprocess_curve(target_data, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth)

    # Definir tamanho alvo para interpolação (pode ser o da curva target)
    target_len = len(target_data_norm)

    # Interpolar todas para o mesmo tamanho
    curvas_interp = [interpolate_curve(curva, target_len) for curva in curvas_norm]
    target_data_interp = interpolate_curve(target_data_norm, target_len)

    # Calcular mínimo global entre todas as curvas interpoladas e target
    todos_valores = np.concatenate(curvas_interp + [target_data_interp])
    min_global = np.min(todos_valores)

    # Ajustar curvas para que mínimo global seja 0
    curvas_alinhadas = [curva - min_global for curva in curvas_interp]
    target_alinhada = target_data_interp - min_global

    patched_figure = Patch()

    patched_figure["data"][0]["y"] = target_alinhada

    for idx, curva in enumerate(curvas_alinhadas):
        patched_figure["data"][idx+1]["y"] = curva

    return patched_figure


@callback(
    Output("home_background_graph", "figure", allow_duplicate=True),
    Output("home_dtw_result_data", "data"),
    Output("home_peaks_intervals", "data"),
    Input("home_apply_dtw_btn", "n_clicks"),
    State("home_data_graph", "figure"),
    State("home_diff_std_input", "value"),
    State("home_merge_gap_input", "value"),
    State("home_relative_height_input", "value"),
    State("home_smooth_window_input", "value"),
    Input("home_n_apply_smooth_input", "value"),
    State("home_graph_raw_data", "data"),
    State("url", "search"),
    running=[
        (Output("home_background_graph_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, False),
        (Output("home_min_curves_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def home_apply_dtw(
    nc1: int,
    fig: dict,
    diff_std: float,
    gap: int,
    relative_height: float,
    smooth_value: int,
    n_apply_smooth: int,
    loaded_data: dict,
    search: str
) -> tuple[Patch, dict, dict]:
    """
    Function responsible for applying the DTW algorithm, plotting the result distances and difference of the target curve and each
    other day into the `home_background_graph`, storing the data of the DTW into the store `home_dtw_result_data` and the peaks
    intervals into the store `home_peaks_intervals`.

    Parameters
    ----------
    nc1 : int
        Input for when apply DTW button is clicked.

    fig : dict
        The current state of the graph figure of `home_data_graph`.
            {
                "data": ...
                "layout": ...
            }

    diff_std : float
        The multiplier of the standard deviation to be used to find peaks.

    gap : int
        The distance of points to merge peaks if they are too close to each other.

    relative_height : float
        The % of height used to find peaks.

    smooth_value : int
        Number of neighbours to apply the smoothing.
    
    "n_apply_smooth": int
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    date: str
        The date of the curve to be analyzed (YYYY-MM-DD format).

    loaded_data: dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list of float
                        X-axis data of the target curve.
                    "table": Fits table
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list of list of float
                        X-axis data of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }
            
    search : str
        The extra parameters of the url.

    Returns
    -------
    Patch
        A patched figure to update the curves of the background graph with the background curves.

    dict
        A dict to store the DTW obtained data::
        
            {
                "resultados": list of tuple[int, float]
                    List of each index and distance of each curve to the target.
                "smooth_window": int
                    Number of neighbours used to apply the smoothing.
                "n_apply_smooth": int
                    Number of iterations to apply the smoothing with `smooth_window` neighbours.
            }

    dict
        A dict with the list of all positive and negative peaks::

            {
                "pos": list of list of tuple[float, float]
                    A list with all the positive peaks (tuples) of all curves.
                "neg": list of list of tuple[float, float]
                    A list with all the negative peaks (tuples) of all curves.
            }
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    if lang == "en":
        translated = TRANSLATIONS["en"]
    else:
        translated = TRANSLATIONS["pt"]

    target_alinhada = fig["data"][6]["y"]
    curvas_alinhadas = [data["y"] for data in fig["data"][:6]]

    resultados = [calcular_fastdtw(i, curva, target_alinhada) for i, curva in enumerate(curvas_alinhadas)]

    dtw_data = {
        "resultados": resultados,
        "smooth_window": smooth_value,
        "n_apply_smooth": n_apply_smooth,
    }

    patched_figure = Patch()

    patched_figure["layout"]["shapes"] = []

    distancias_sorted = sorted(resultados, key=lambda x: x[1])

    curvas_diff = []

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = np.array(target_alinhada) - np.array(curvas_alinhadas[idx])
        curvas_diff.append(diff)

    # Guardar intervalos merged de todas as curvas
    intervals_all_pos = []
    intervals_all_neg = []

    target_day = loaded_data["target"]["day"]

    curve_days = loaded_data["curves"]["days"]

    shapes = []

    ranges = [[0.85, 1], [0.68, 0.84], [0.51, 0.67], [0.34, 0.5], [0.17, 0.33], [0, 0.16]]

    annotations = []

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = curvas_diff[i]
        patched_figure["data"][i*3]["y"] = diff
        patched_figure["data"][i*3]["name"] = f"[TARGET] {target_day} - {translated['graphs']['curve']} {curve_days[idx]} (FastDTW={dist:.2f})"
        patched_figure["data"][i*3+1]["y"] = [np.std(diff) * diff_std, np.std(diff) * diff_std]
        patched_figure["data"][i*3+2]["y"] = [-(np.std(diff) * diff_std), -(np.std(diff) * diff_std)]
        patched_figure["data"][i*3+1]["x"] = [0, len(diff)]
        patched_figure["data"][i*3+2]["x"] = [0, len(diff)]

        annotations.append(
            {
                "x": 0,           # fraction: 0 = left
                "y": 0,           # fraction: 0 = bottom
                "xref": f"x{i+1} domain",
                "yref": f"y{i+1} domain",
                "xanchor": "left",
                "yanchor": "bottom",
                "text": f"{curve_days[idx]}<br>FastDTW={dist:.2f}",
                "showarrow": False,
                "font": {"size": 12, "color": "white"},
                "bgcolor": "#1E6F88",
                "borderpad": 4,
                "opacity": 0.8
            }
        )

        peaks_pos, _ = find_peaks(diff, height=np.std(diff) * diff_std, threshold = 0)
        peaks_neg, _ = find_peaks(-diff, height=np.std(diff) * diff_std, threshold = 0)

        intervals_pos = []
        intervals_neg = []

        if len(peaks_pos) > 0:
            results_pos = peak_widths(diff, peaks_pos, rel_height=relative_height)
            intervals_pos.extend(zip(results_pos[2], results_pos[3]))

        if len(peaks_neg) > 0:
            results_neg = peak_widths(-diff, peaks_neg, rel_height=relative_height)
            intervals_neg.extend(zip(results_neg[2], results_neg[3]))

        merged_pos = merge_intervals(intervals_pos, gap=gap)
        merged_neg = merge_intervals(intervals_neg, gap=gap)

        intervals_all_pos.append(merged_pos)
        intervals_all_neg.append(merged_neg)

        for start, end in merged_pos:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": start,
                    "x1": end,
                    "y0": ranges[i][0],
                    "y1": ranges[i][1],
                    "fillcolor": "cyan",
                    "opacity": 0.15,
                    "line": {"width": 0},
                    "xaxis": f"x{i+1}",
                    "yaxis": f"y{i+1}"
                }
            )

        for start, end in merged_neg:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": start,
                    "x1": end,
                    "y0": ranges[i][0],
                    "y1": ranges[i][1],
                    "fillcolor": "red",
                    "opacity": 0.15,
                    "line": {"width": 0},
                    "xaxis": f"x{i+1}",
                    "yaxis": f"y{i+1}"
                }
            )

    patched_figure["layout"]["shapes"] = shapes
    patched_figure["layout"]["annotations"] = annotations

    all_peaks = {
        "pos": intervals_all_pos,
        "neg": intervals_all_neg,
    }

    return patched_figure, dtw_data, all_peaks


@callback(
    Output("home_background_graph", "figure", allow_duplicate=True),
    Output("home_peaks_intervals", "data", allow_duplicate=True),
    Input("home_diff_std_input", "value"),
    Input("home_merge_gap_input", "value"),
    Input("home_relative_height_input", "value"),
    State("home_graph_raw_data", "data"),
    State("home_data_graph", "figure"),
    State("home_dtw_result_data", "data"),
    State("url", "search"),
    running=[
        (Output("home_background_graph_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, False),
        (Output("home_min_curves_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def home_update_dtw(
    diff_std: float,
    gap: int,
    relative_height: float,
    loaded_data: dict,
    fig: dict,
    dtw_data: dict,
    search: str
) -> tuple[Patch, dict]:
    """
    Function responsible for reapplying the DTW algorithm and updating the background graph data
    given changes on the `diff_std`, `gap` or `relative_height` values, plotting into the `home_background_graph`
    and storing the new peaks intervals into the store `home_peaks_intervals`.

    Parameters
    ----------
    diff_std : float
        The multiplier of the standard deviation to be used to find peaks.

    gap : int
        The distance of points to merge peaks if they are too close to each other.

    relative_height : float
        The % of height used to find peaks.

    loaded_data: dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list of float
                        X-axis data of the target curve.
                    "table": Fits table
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list of list of float
                        X-axis data of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }

    fig : dict
        The current state of the graph figure of `home_data_graph`::

            {
                "data": ...
                "layout": ...
            }

    dtw_data: dict
        A dict to store the DTW obtained data::

            {
                "resultados": list of tuple[int, float]
                    List of each index and distance of each curve to the target.
                "smooth_window": int
                    Number of neighbours used to apply the smoothing.
                "n_apply_smooth": int
                    Number of iterations to apply the smoothing with `smooth_window` neighbours.
            }
     
    search : str
        The extra parameters of the url.


    Returns
    -------
    Patch
        A patched figure to update the curves of the background graph with the background curves.

    dict
        A dict with the list of all positive and negative peaks::

            {
                "pos": list of list of tuple[float, float]
                    A list with all the positive peaks (tuples) of all curves.
                "neg": list of list of tuple[float, float]
                    A list with all the negative peaks (tuples) of all curves.
            }
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    if lang == "en":
        translated = TRANSLATIONS["en"]
    else:
        translated = TRANSLATIONS["pt"]

    target_alinhada = fig["data"][0]["y"]
    curvas_alinhadas = [data["y"] for data in fig["data"][1:]]
    smooth_value = dtw_data["smooth_window"]
    resultados = dtw_data["resultados"]

    patched_figure = Patch()

    patched_figure["layout"]["shapes"] = []

    distancias_sorted = sorted(resultados, key=lambda x: x[1])

    curvas_diff = []

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = np.array(target_alinhada) - np.array(curvas_alinhadas[idx])
        curvas_diff.append(diff)

    # Guardar intervalos merged de todas as curvas
    intervals_all_pos = []
    intervals_all_neg = []

    target_day = loaded_data["target"]["day"]

    curve_days = loaded_data["curves"]["days"]

    shapes = []

    ranges = [[0.85, 1], [0.68, 0.84], [0.51, 0.67], [0.34, 0.5], [0.17, 0.33], [0, 0.16]]

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = curvas_diff[i]
        patched_figure["data"][i*3]["y"] = diff
        patched_figure["data"][i*3]["name"] = f"[TARGET] {target_day} - {translated['graphs']['curve']} {curve_days[idx]} (FastDTW={dist:.2f})"
        patched_figure["data"][(i*3)+1]["y"] = [np.std(diff) * diff_std, np.std(diff) * diff_std]
        patched_figure["data"][(i*3)+2]["y"] = [-(np.std(diff) * diff_std), -(np.std(diff) * diff_std)]

        peaks_pos, _ = find_peaks(diff, height=np.std(diff) * diff_std, threshold = 0)
        peaks_neg, _ = find_peaks(-diff, height=np.std(diff) * diff_std, threshold = 0)

        intervals_pos = []
        intervals_neg = []

        if len(peaks_pos) > 0:
            results_pos = peak_widths(diff, peaks_pos, rel_height=relative_height)
            intervals_pos.extend(zip(results_pos[2], results_pos[3]))

        if len(peaks_neg) > 0:
            results_neg = peak_widths(-diff, peaks_neg, rel_height=relative_height)
            intervals_neg.extend(zip(results_neg[2], results_neg[3]))

        merged_pos = merge_intervals(intervals_pos, gap=gap)
        merged_neg = merge_intervals(intervals_neg, gap=gap)

        intervals_all_pos.append(merged_pos)
        intervals_all_neg.append(merged_neg)

        for start, end in merged_pos:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": start,
                    "x1": end,
                    "y0": ranges[i][0],
                    "y1": ranges[i][1],
                    "fillcolor": "cyan",
                    "opacity": 0.3,
                    "line": {"width": 0},
                    "xaxis": f"x{i+1}",
                    "yaxis": f"y{i+1}"
                }
            )

        for start, end in merged_neg:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": start,
                    "x1": end,
                    "y0": ranges[i][0],
                    "y1": ranges[i][1],
                    "fillcolor": "red",
                    "opacity": 0.3,
                    "line": {"width": 0},
                    "xaxis": f"x{i+1}",
                    "yaxis": f"y{i+1}"
                }
            )

    patched_figure["layout"]["shapes"] = shapes

    all_peaks = {
        "pos": intervals_all_pos,
        "neg": intervals_all_neg,
    }

    return patched_figure, all_peaks


@callback(
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Output("home_results_log", "children", allow_duplicate=True),
    Output("home_events_data", "data"),
    Input("home_get_results_btn", "n_clicks"),
    State("home_peaks_intervals", "data"),
    State("home_graph_raw_data", "data"),
    State("home_min_curves_input", "value"),
    State("home_dtw_result_data", "data"),
    State("url", "search"),
    running=[
        (Output("home_result_graph_loading_overlay", "visible"), True, False),
        (Output("home_result_background_graph_loading_overlay", "visible"), True, False),
        (Output("home_result_log_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, False),
        (Output("home_min_curves_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
        (Output("home_download_button", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def home_get_results(
    nc1: int,
    peaks_intervals: float,
    loaded_data: dict,
    min_curves: int,
    dtw_data: dict,
    search: str,
) -> tuple[Patch, Patch, list[dbc.ListGroupItem]]:
    """
    Function responsible for generating the results data and plotting into the graphs `home_results_graph` and
    `home_results_background_graph` and also displaying the logs of the peaks inside the `home_results_log` component.

    Parameters
    ----------
    nc1 : int
        Input for when get results button is clicked.

    peaks_intervals: dict
        A dict with the list of all positive and negative peaks::

            {
                "pos": list of list of tuple[float, float]
                    A list with all the positive peaks (tuples) of all curves.
                "neg": list of list of tuple[float, float]
                    A list with all the negative peaks (tuples) of all curves.
            }

    loaded_data: dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list of float
                        X-axis data of the target curve.
                    "table": Fits table
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list of list of float
                        X-axis data of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }

    min_curves: int
        Number of minimum curves to have a peak at that period in time.

    dtw_data: dict
        A dict to store the DTW obtained data::

            {
                "resultados": list of tuple[int, float]
                    List of each index and distance of each curve to the target.
                "smooth_window": int
                    Number of neighbours used to apply the smoothing.
                "n_apply_smooth": int
                    Number of iterations to apply the smoothing with `smooth_window` neighbours.
            }

    search : str
        The extra parameters of the url.


    Returns
    -------
    Patch
        A patched figure to update the curves of the result graph.

    Patch
        A patched figure to update the curves of the result background graph.

    list of dbc.ListGroupItem
        A list of logs of each estimated peak (Initial time - Final time)

    dict
        A dict with the data of each possible flare stored in `home_events_data`::

            {
                "x": list of datetime
                    List of the dates of the target event.
                "y": list of float
                    List of the intensity of the background subtraction of each event.
            }
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    if lang == "en":
        translated = TRANSLATIONS["en"]
    else:
        translated = TRANSLATIONS["pt"]

    # --- Getting curve data ---

    smooth_window = dtw_data["smooth_window"]
    n_apply_smooth = dtw_data["n_apply_smooth"]
    
    target_data = loaded_data["target"]["data"]
    target_table = loaded_data["target"]["table"]
    target_day = loaded_data["target"]["day"]
    curve_data_list = loaded_data["curves"]["data_list"]
    datetime_list, datetime_str = generate_datetime_list(target_table)

    common_pos = find_common_intervals_precise(peaks_intervals["pos"], min_curves)
    common_neg = find_common_intervals_precise(peaks_intervals["neg"], min_curves)

    # --- Results ---

    patched_figure = Patch()

    target_y = apply_smooth(target_data, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth)

    # --- Background ---

    background_patched_figure = Patch()
    
    target_len = len(target_data)

    curves_raw_interp = [interpolate_curve(curve, target_len) for curve in curve_data_list]
    curves_raw_smooth = [apply_smooth(curve, smooth_window, n_apply_smooth) for curve in curves_raw_interp]
    background_curve = np.median(curves_raw_smooth, axis=0)
    background_subtracted = np.array(target_data) - np.array(background_curve)

    # --- Getting logs ---

    shapes = []
    logs = []
    background_curves = []

    for idx, (start, end) in enumerate(common_pos):
        logs.append(
            dbc.ListGroupItem(
                f"{translated["logs"]["possible_flare"]}: {datetime_str[int(start)]} - {datetime_str[int(end)]}",
                id={"type": "possible_flare", "index": idx},
                className="home-results-log-up"
            ),
        )
        shapes.append(
            {
                "type": "rect",
                "xref": "x",
                "yref": "paper",
                "x0": datetime_str[int(start)],
                "x1": datetime_str[int(end)],
                "y0": 0,
                "y1": 1,
                "fillcolor": "cyan",
                "opacity": 0.3,
                "line": {"width": 0},
            }
        )
        start_time = max(0, start - 1000)
        end_time = min(len(datetime_str), end + 1000)
        background_curves.append(
            {
                "x": datetime_str[int(start_time):int(end_time)],
                "y": background_subtracted[int(start_time):int(end_time)]
            }
        )

    for start, end in common_neg:
        logs.append(
            dbc.ListGroupItem(
                f"{translated["logs"]["possible_problem"]}: {datetime_str[int(start)]} - {datetime_str[int(end)]}",
                className="home-results-log-down"
            ),
        )
        shapes.append(
            {
                "type": "rect",
                "xref": "x",
                "yref": "paper",
                "x0": datetime_str[int(start)],
                "x1": datetime_str[int(end)],
                "y0": 0,
                "y1": 1,
                "fillcolor": "red",
                "opacity": 0.3,
                "line": {"width": 0},
            }
        )

    # --- Plot ---

    
    hover_template = "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"
    patched_figure["data"] = [
        go.Scatter(
            y=target_data,
            x=datetime_list,
            mode='lines',
            name=f"[TARGET] {target_day}",
            line=dict(width=1, color="#bdb4fc"),
            opacity=0.5,
            hovertemplate=hover_template,
        ),
        go.Scatter(
            y=target_y,
            x=datetime_list,
            mode='lines',
            name=f"[TARGET] {target_day}",
            line=dict(width=2, color="black"),
            opacity=1,
            hovertemplate=hover_template,
        )
    ]

    if background_curves:
        background_patched_figure["data"] = [
            go.Scatter(
                y=background_curves[0]["y"],
                x=background_curves[0]["x"],
                mode='lines',
                name=f"[TARGET] {target_day}",
                line=dict(width=2, color=BACKGROUND_LINE_COLOR),
                opacity=1,
                hovertemplate=hover_template,
            ),
        ]

    patched_figure["layout"]["shapes"] = shapes

    return patched_figure, background_patched_figure, logs, background_curves


@callback(
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Input({"type": "possible_flare", "index": ALL}, "n_clicks"),
    State("home_events_data", "data"),
    prevent_initial_call=True,
)
def home_load_possible_flare(nc1: list[int], events_data: dict) -> Patch:
    """
    Function responsible for loading the event into the background graph `home_results_background_graph`
    when clicking on a possible flare in the logs.

    Parameters
    ----------
    nc1 : list of int
        List of logs for when get one of them is clicked.

    events_data : dict
        A dict with the data of each possible flare stored in `home_events_data`::

            {
                "x": list of datetime
                    List of the dates of the target event.
                "y": list of float
                    List of the intensity of the background subtraction of each event.
            }


    Returns
    -------
    Patch
        A patched figure to update the curve of the result background graph given a possible event.
    """
    if any(events_data):
        triggered_id = callback_context.triggered_id
        idx = int(triggered_id["index"])

        patched_figure = Patch()

        patched_figure["data"][0]["x"] = events_data[idx]["x"]
        patched_figure["data"][0]["y"] = events_data[idx]["y"]

        return patched_figure
    return no_update