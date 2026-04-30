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
from datetime import datetime, timedelta
from dash_iconify import DashIconify
from scipy.signal import find_peaks, peak_widths
from urllib.parse import parse_qs

from src.components.cards import generate_card
from src.components.logs import generate_new_log
from src.functions.data_treatment import *
from src.functions.data_validation import *
from src.functions.database import *
from src.constants.graph import *
from src.constants.dates import *
from src.constants.translations import TRANSLATIONS

register_page(__name__, path="/")

def layout(**kwargs):
    if kwargs.get("lang") and kwargs.get("lang") in TRANSLATIONS:
        lang = kwargs.get("lang")
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
                minDate=DATA_INICIAL,
                maxDate=DATA_FINAL,
                disabledDates=DATAS_FALTANTES,
                className="custom-input home-date-input",
                valueFormat="DD/MM/YYYY",
                hideOutsideDates=True, 
            ),
            dmc.Select(
                id="home_data_select",
                label=translated["components"]["data_select"],
                value="TBL45",
                data=[
                    {"value": "TBL45", "label": "TBL 45"},
                    {"value": "TBR45", "label": "TBR 45"},
                    {"value": "TBL90", "label": "TBL 90"},
                    {"value": "TBR90", "label": "TBR 90"},
                ],
                className="home-data-type-select",
            ),
            dmc.Select(
                id="home_interpolation_select",
                label=translated["components"]["interpolation_select"]["label"],
                value="original",
                data=[
                    {"value": "original", "label": translated["components"]["interpolation_select"]["values"]["original"]},
                    {"value": "refined", "label": translated["components"]["interpolation_select"]["values"]["refined"]},
                    {"value": "to_zero", "label": translated["components"]["interpolation_select"]["values"]["to_zero"]},
                ],
                className="home-interpolation-type-select",
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
                                src="/assets/sol.svg",
                                h=200,
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
                        value=25,
                        min=1,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["iteration_quantity"],
                        id="home_n_apply_smooth_input",
                        value=4,
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
                        src="/assets/sol.svg",
                        h=200,
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
                        value=3,
                        min=0.1,
                        max=10,
                        disabled=True,
                        debounce=True,
                        decimalScale=2,
                        step=0.1,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["number_of_segments"],
                        id="home_number_of_segments_input",
                        value=8,
                        min=1,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["quantity_mean_std"],
                        id="home_quantity_mean_std_input",
                        value=6,
                        min=1,
                        max=8,
                        disabled=True,
                        debounce=True,
                        allowDecimal=False,
                    ),
                ],
                className="same-line home-inputs-blocks"
            ),
            html.Div(
                [
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
                        value=0.55,
                        min=0,
                        disabled=True,
                        debounce=True,
                        decimalScale=2,
                        step=0.01,
                    ),
                    dmc.NumberInput(
                        label=translated["components"]["avoid_border"],
                        id="home_avoid_border_input",
                        value=6,
                        min=0.01,
                        max=30,
                        disabled=True,
                        debounce=True,
                        decimalScale=2,
                        step=0.1,
                    ),
                ],
                className="same-line home-inputs-blocks"
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dmc.NumberInput(
                                label=translated["components"]["min_curves"],
                                id="home_min_curves_input",
                                value=70,
                                min=1,
                                max=100,
                                disabled=True,
                                debounce=True,
                                allowDecimal=False,
                            ),
                            dmc.NumberInput(
                                label=translated["components"]["dtw_weight"],
                                id="home_dtw_weight_input",
                                value=1.2,
                                min=0.1,
                                max=5,
                                disabled=True,
                                debounce=True,
                                decimalScale=2,
                                step=0.1,
                            ),
                        ],
                        className="same-line"
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
                                    dmc.TabsTab(translated["components"]["results_tab"]["day"], value="day"),
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
                                                        src="/assets/sol.svg",
                                                        h=200,
                                                    ),
                                                },
                                                overlayProps={"radius": "sm", "blur": 2},
                                                visible=False,
                                                zIndex=10,
                                            ),
                                            dcc.Graph(
                                                id="home_results_graph",
                                                config=PLOT_CONFIG,
                                                figure=generate_result_fig_properties(lang),
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
                                                        src="/assets/sol.svg",
                                                        h=200,
                                                    ),
                                                },
                                                overlayProps={"radius": "sm", "blur": 2},
                                                visible=False,
                                                zIndex=10,
                                            ),
                                            dcc.Graph(
                                                id="home_results_background_graph",
                                                config=PLOT_CONFIG,
                                                figure=generate_result_fig_properties(lang),
                                            )
                                        ],
                                        className="home-results-graph"
                                    ),
                                ],
                                value="background",
                                className="home-results-graph",
                            ),
                            dmc.TabsPanel(
                                [
                                    html.Div(
                                        [
                                            dmc.LoadingOverlay(
                                                id="home_result_day_graph_loading_overlay",
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
                                            dcc.Graph(
                                                id="home_results_day_graph",
                                                config=PLOT_CONFIG,
                                                figure=generate_result_fig_properties(lang),
                                            )
                                        ],
                                        className="home-results-graph"
                                    ),
                                ],
                                value="day",
                                className="home-results-graph",
                            ),
                        ],
                        value="result",
                        id="home_results_tabs",
                        className="home-results-graph",
                    ),
                ],
                className="results-graph-contents",
            ),
            html.Div(
                [
                    dmc.MultiSelect(
                        id="home_results_add_new_log_multiselect",
                        label=translated["logs"]["add_log_label"],
                        value=[],
                        data=[],
                        disabled=True,
                        className="home-results-add-log-multiselect"
                    ),
                    dmc.ActionIcon(
                        [
                            DashIconify(
                                icon="mdi:add-bold",
                                color="#FFFFFF",
                            )
                        ],
                        className="home-results-btn button-style",
                        id="home_results_add_new_log_btn",
                        disabled=True,
                    ),
                ],
                className="same-line home-add-log-container"
            ),
            html.Div(
                [
                    dmc.LoadingOverlay(
                        id="home_result_log_loading_overlay",
                        loaderProps={
                            "variant": "custom",
                            "children": dmc.Image(
                                src="/assets/sol.svg",
                                h=150,
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
                        value="db",
                        data=[
                            {"value": key, "label": value}
                            for key, value in translated["components"]["download_select"]["values"].items()
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
            dcc.Store(id="home_reassign_log_index"),
        ]
    )

    page_notification_container = html.Div(
        [
            dmc.NotificationContainer(id="home_notification_container")
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
                id="home_screen_loading_overlay",
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
            page_notification_container,
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


@callback(
    Output("home_data_graph", "figure"),
    Output("home_background_graph", "figure"),
    Output("home_results_graph", "figure"),
    Output("home_results_background_graph", "figure"),
    Output("home_results_day_graph", "figure"),
    Output("home_graph_raw_data", "data"),
    Output("home_results_log", "children"),
    Output("home_results_add_new_log_multiselect", "data"),
    Output("home_results_add_new_log_multiselect", "value"),
    Output("home_notification_container", "sendNotifications"),
    Input("home_load_data_btn", "n_clicks"),
    State("home_data_select", "value"),
    State("home_interpolation_select", "value"),
    State("home_smooth_window_input", "value"),
    State("home_n_apply_smooth_input", "value"),
    State("home_date_input", "value"),
    State("url", "search"),
    running=[
        (Output("home_screen_loading_overlay", "visible"), True, False),
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, True),
        (Output("home_min_curves_input", "disabled"), True, True),
        (Output("home_number_of_segments_input", "disabled"), True, True),
        (Output("home_quantity_mean_std_input", "disabled"), True, True),
        (Output("home_dtw_weight_input", "disabled"), True, True),
        (Output("home_avoid_border_input", "disabled"), True, True),
        (Output("home_merge_gap_input", "disabled"), True, True),
        (Output("home_relative_height_input", "disabled"), True, True),
        (Output("home_get_results_btn", "disabled"), True, True),
        (Output("home_download_button", "disabled"), True, True),
        (Output("home_results_add_new_log_multiselect", "disabled"), True, True),
        (Output("home_results_add_new_log_btn", "disabled"), True, True),
    ],
    prevent_initial_call=True,
)
def home_load_data(
    nc1: int,
    data_select: str,
    interpolation_select: str,
    smooth_window: int,
    n_apply_smooth: int,
    date: str,
    search: str,
) -> tuple[Patch, dict, dict, dict, dict, dict, list, list, list]:
    """
    Function responsible for loading the data, plotting into the `home_data_graph` and storing
    the raw data of all curves inside the store `home_graph_raw_data`.

    Parameters
    ----------
    nc1 : int
        Input for when load data button is clicked.

    data_select : str
        The position of the curve to be loaded in the fits file. Possible values are::

            - "TBL45"
            - "TBR45"
            - "TBL90"
            - "TBR90"

    interpolation_select : str
        The type of interpolation to be applied to the curves. Possible values are::

            - "original": a "not so good" interpolation for data retrieval, but better for flare detection.
            - "refined": a right interpolation of data, but sometimes it can oversmooth important features.
            - "to_zero": a interpolation that forces gaps to be 0.

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
        FIG_PROPERTIES to reset the results day graph.

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
                    "data_times": list of Datetimes
                        A list for the datetimes of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }

    list
        Empty list to reset the results log.

    list
        List of days for the add log multiselect.

    list
        Empty list to reset the add log multiselect.
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
        translated = TRANSLATIONS["pt"]

    all_files, target_file_to_load = prepare_versos_dataset(target_date_str=date)

    if target_file_to_load is None:
        notification = [dict(
            id="date_not_found_notification",
            title = translated["notifications"]["date_not_found"]["title"],
            message = translated["notifications"]["date_not_found"]["message"],
            color = "red",
            action = "show",
            autoClose=10000,
            position="top-center",
        )]
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            notification,
        )
    
    if len(all_files) < 6:
        notification = [dict(
            id="not_enough_curves_notification",
            title = translated["notifications"]["not_enough_curves"]["title"],
            message = translated["notifications"]["not_enough_curves"]["message"],
            color = "red",
            action = "show",
            autoClose=10000,
            position="top-center",
        )]
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            notification,
        )

    curve_data_list = []
    curve_days = []
    curve_tables = []

    for file in all_files:
        data, full_table, day = load_fits_data(file, data_select)

        if file == target_file_to_load:
            target_data = data
            target_full_table = full_table
            target_day = day
            continue

        curve_data_list.append(data)
        curve_days.append(day)
        curve_tables.append(full_table)

    loaded_data = {
        "target": {
            "data": to_list(target_data),
            "table": fits_table_to_list_of_lists(target_full_table),
            "day": target_day
        },
        "curves": {
            "data_list": [to_list(curva) for curva in curve_data_list],
            "data_times": build_curve_time_arrays_from_target_day(
                curve_tables,
                target_day
            ),
            "days": curve_days,
        }
    }

    target_datetime_list, datetime_str = generate_datetime_list(loaded_data["target"]["table"])

    # ======== Pré-processar e interpolar todas ========

    # Pré-processar todas as curvas e target (Z-score + Smooth)
    results = [
        preprocess_curve(
            curva,
            curva_datetimes,
            smooth_window=smooth_window,
            n_apply_smooth=n_apply_smooth,
            target=False
        )
        for curva, curva_datetimes in zip(curve_data_list, loaded_data["curves"]["data_times"])
    ]

    # unpack dos resultados em duas listas
    curvas_norm, treated_curves_datetime = zip(*results)

    # Opcional: Converter para listas (o zip retorna tuplas por padrão)
    curvas_norm = list(curvas_norm)
    treated_curves_datetime = list(treated_curves_datetime)
    
    target_data_norm, _ = preprocess_curve(target_data, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth)

    # Definir tamanho alvo para interpolação
    target_len = len(target_data_norm)

    # Interpolar todas para o mesmo tamanho (Injetando 0.0 nos gaps se refined)
    if interpolation_select == "original":
        curvas_interp = [interpolate_curve(curva, target_len) for curva in curvas_norm]
        target_data_interp = interpolate_curve(target_data_norm, target_len)
    elif interpolation_select == "refined":
        curvas_interp = [
            interpolate_curve_to_target_time(
                target_datetime_list,
                curve_datetime_list,
                curva_norm,
            )
            for curva_norm, curve_datetime_list in zip(
                curvas_norm, treated_curves_datetime
            )
        ]
        target_data_interp = target_data_norm
    elif interpolation_select == "to_zero":
        curvas_interp = [
            interpolate_gated_to_zero(
                target_datetime_list,
                curve_datetime_list,
                curva_norm,
            )
            for curva_norm, curve_datetime_list in zip(
                curvas_norm, treated_curves_datetime
            )
        ]
        target_data_interp = target_data_norm
    else:
        curvas_interp = [interpolate_curve(curva, target_len) for curva in curvas_norm]
        target_data_interp = interpolate_curve(target_data_norm, target_len)

    # Calcular mínimo global entre todas as curvas e target
    todos_valores = np.concatenate(curvas_interp + [target_data_interp])
    min_global = np.min(todos_valores)

    # Ajustar curvas para que mínimo global seja 0 e restaurar gaps
    curvas_alinhadas = []
    for curva in curvas_interp:
        c_shifted = curva - min_global
        if interpolation_select == "to_zero":
            c_shifted[curva == 0] = 0
        curvas_alinhadas.append(c_shifted)

    target_alinhada = target_data_interp - min_global

    patched_figure = Patch()

    patched_figure["data"] = []

    hover_template = f"{translated['graphs']['point']} " + "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"

    for idx, curva in enumerate(curvas_alinhadas):
        patched_figure["data"].append(
            go.Scatter(
                y=curva,
                x=datetime_str,
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
            x=datetime_str,
            mode='lines',
            name=f"[TARGET] {target_day}",
            line=dict(width=2.5),
            opacity=1,
            hovertemplate=hover_template,
        )
    )

    events_data = [
        {"value": f"{idx}", "label": f"{curve_day_label}"}
        for idx, curve_day_label in enumerate(curve_days)
    ]

    return (
        patched_figure,
        generate_background_fig_properties(lang),
        generate_result_fig_properties(lang),
        generate_result_fig_properties(lang),
        generate_result_fig_properties(lang),
        loaded_data,
        [],
        events_data,
        [],
        no_update,
    )

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

    loaded_data : dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list[float]
                        X-axis data of the target curve.
                    "table": list[list]
                        The FITS table of the target curve (as list of lists).
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list[list[float]]
                        X-axis data of the curves to be compared.
                    "data_times": list[np.ndarray]
                        A list for the datetimes of the curves to be compared.
                    "days": list[str]
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

    for idx, curva in enumerate(curvas_alinhadas[:-1]):
        patched_figure["data"][idx]["y"] = curva

    patched_figure["data"][6]["y"] = target_alinhada


    return patched_figure


@callback(
    Output("home_background_graph", "figure", allow_duplicate=True),
    Output("home_dtw_result_data", "data"),
    Output("home_peaks_intervals", "data"),
    Input("home_apply_dtw_btn", "n_clicks"),
    State("home_data_graph", "figure"),
    State("home_diff_std_input", "value"),
    State("home_dtw_weight_input", "value"),
    State("home_number_of_segments_input", "value"),
    State("home_quantity_mean_std_input", "value"),
    State("home_avoid_border_input", "value"),
    State("home_merge_gap_input", "value"),
    State("home_relative_height_input", "value"),
    State("home_smooth_window_input", "value"),
    State("home_n_apply_smooth_input", "value"),
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
        (Output("home_number_of_segments_input", "disabled"), True, False),
        (Output("home_quantity_mean_std_input", "disabled"), True, False),
        (Output("home_dtw_weight_input", "disabled"), True, False),
        (Output("home_avoid_border_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
        (Output("home_results_add_new_log_multiselect", "disabled"), True, True),
        (Output("home_results_add_new_log_btn", "disabled"), True, True),
    ],
    prevent_initial_call=True,
)
def home_apply_dtw(
    nc1: int,
    fig: dict,
    diff_std: float,
    weight: float,
    number_of_segments: int,
    quantity_mean_std: int,
    avoid_border: float,
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
        The current state of the graph figure of `home_data_graph`::

            {
                "data": list[dict]
                    List of trace dictionaries.
                "layout": dict
                    Layout configuration.
            }

    diff_std : float
        The multiplier of the standard deviation to be used to find peaks.

    weight : float
        The weight for the DTW distances.

    number_of_segments : int
        Number of segments that the curve will be divided for analysing.

    quantity_mean_std : int
        Number of stds selected from segments to take the mean.

    avoid_border : float
        Value to not consider border (0 - 30)%.

    gap : int
        The distance of points to merge peaks if they are too close to each other.

    relative_height : float
        The % of height used to find peaks.

    smooth_value : int
        Number of neighbours to apply the smoothing.
    
    n_apply_smooth : int
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    loaded_data : dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list[float]
                        X-axis data of the target curve.
                    "table": list[list]
                        The FITS table of the target curve (as list of lists).
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list[list[float]]
                        X-axis data of the curves to be compared.
                    "data_times": list[np.ndarray]
                        A list for the datetimes of the curves to be compared.
                    "days": list[str]
                        The day of each curve.
                }
            }
            
    search : str
        The extra parameters of the url.

    Returns
    -------
    tuple[Patch, dict, dict]
        patched_figure : Patch
            A patched figure to update the curves of the background graph with the background curves.

        dtw_data : dict
            A dict to store the DTW obtained data::
            
                {
                    "resultados": list[tuple[int, float]]
                        List of each index and distance of each curve to the target.
                    "smooth_window": int
                        Number of neighbours used to apply the smoothing.
                    "n_apply_smooth": int
                        Number of iterations to apply the smoothing with `smooth_window` neighbours.
                }

        all_peaks : dict
            A dict with the list of all positive and negative peaks::

                {
                    "pos": dict
                        - "interval": list of tuples [(start, end), ...]
                        - "weight": float, weight of this interval (0-100)
                        - "curve": any, identifier of the curve
                    "neg": dict
                        - "interval": list of tuples [(start, end), ...]
                        - "weight": float, weight of this interval (0-100)
                        - "curve": any, identifier of the curve
                }
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
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

    total_dist = sum(1 / x[1]**weight for x in distancias_sorted)

    _, datetime_str = generate_datetime_list(loaded_data["target"]["table"])

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = curvas_diff[i].copy()

        patched_figure["data"][i*3]["y"] = curvas_diff[i]
        patched_figure["data"][i*3]["x"] = datetime_str
        patched_figure["data"][i*3]["name"] = f"[TARGET] {target_day} - {translated['graphs']['curve']} {curve_days[idx]} (FastDTW={dist:.2f})"

        # Ignore first and last % of the curve
        safe_cut_percentage = max(avoid_border, 0.01)
        cut = int((safe_cut_percentage/100) * len(diff))
        diff[:cut] = 0
        diff[-cut:] = 0

        curve_std = find_std(diff, number_of_segments, quantity_mean_std)

        patched_figure["data"][i*3+1]["y"] = [curve_std * diff_std, curve_std * diff_std]
        patched_figure["data"][i*3+2]["y"] = [-(curve_std * diff_std), -(curve_std * diff_std)]
        patched_figure["data"][i*3+1]["x"] = [datetime_str[0], datetime_str[-1]]
        patched_figure["data"][i*3+2]["x"] = [datetime_str[0], datetime_str[-1]]

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

        peaks_pos, _ = find_peaks(diff, height=curve_std * diff_std, threshold = 0)
        peaks_neg, _ = find_peaks(-diff, height=curve_std * diff_std, threshold = 0)

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

        intervals_all_pos.append(
            {
                "interval": merged_pos,
                "weight": (1 / dist**weight) / total_dist * 100,
                "curve": idx
            }
        )
        intervals_all_neg.append(
            {
                "interval": merged_neg,
                "weight": (1 / dist**weight) / total_dist * 100,
                "curve": idx
            }
        )

        for start, end in merged_pos:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": datetime_str[int(start)],
                    "x1": datetime_str[int(end)],
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
                    "x0": datetime_str[int(start)],
                    "x1": datetime_str[int(end)],
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
    Output("home_quantity_mean_std_input", "max"),
    Output("home_quantity_mean_std_input", "value"),
    Input("home_diff_std_input", "value"),
    Input("home_number_of_segments_input", "value"),
    Input("home_quantity_mean_std_input", "value"),
    Input("home_dtw_weight_input", "value"),
    Input("home_avoid_border_input", "value"),
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
        (Output("home_number_of_segments_input", "disabled"), True, False),
        (Output("home_quantity_mean_std_input", "disabled"), True, False),
        (Output("home_dtw_weight_input", "disabled"), True, False),
        (Output("home_avoid_border_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def home_update_dtw(
    diff_std: float,
    number_of_segments: int,
    quantity_mean_std: int,
    weight: float,
    avoid_border: float,
    gap: int,
    relative_height: float,
    loaded_data: dict,
    fig: dict,
    dtw_data: dict,
    search: str
) -> tuple[Patch, dict, int, int]:
    """
    Function responsible for reapplying the DTW algorithm and updating the background graph data
    given changes on the `diff_std`, `gap` or `relative_height` values, plotting into the `home_background_graph`
    and storing the new peaks intervals into the store `home_peaks_intervals`.

    Parameters
    ----------
    diff_std : float
        The multiplier of the standard deviation to be used to find peaks.

    number_of_segments : int
        Number of segments that the curve will be divided for analysing.

    quantity_mean_std : int
        Number of stds selected from segments to take the mean.

    weight : float
        The weight for the DTW distances.

    avoid_border : float
        Value to not consider border (0 - 30)%.

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
                    "data_times": list of Datetimes
                        A list for the datetimes of the curves to be compared.
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
                "pos": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
                "neg": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
            }

    int
        Max value possible for quantity_mean_std in case number_of_segments changed.

    int
        New value for quantity_mean_std in case number_of_segments changed and now is lower than the first.
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
        translated = TRANSLATIONS["pt"]

    target_alinhada = fig["data"][6]["y"]
    curvas_alinhadas = [data["y"] for data in fig["data"][:6]]
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
    _, datetime_str = generate_datetime_list(loaded_data["target"]["table"])

    shapes = []

    ranges = [[0.85, 1], [0.68, 0.84], [0.51, 0.67], [0.34, 0.5], [0.17, 0.33], [0, 0.16]]

    total_dist = sum(1 / x[1]**weight for x in distancias_sorted)

    # Validating the quantity_mean_std if number_of_segments was changed:
    if number_of_segments < quantity_mean_std:
        quantity_mean_std = number_of_segments

    for i, (idx, dist) in enumerate(distancias_sorted):
        diff = curvas_diff[i]

        # Ignore first and last % of the curve
        safe_cut_percentage = max(avoid_border, 0.01)
        cut = int((safe_cut_percentage/100) * len(diff))
        diff[:cut] = 0
        diff[-cut:] = 0

        curve_std = find_std(diff, number_of_segments, quantity_mean_std)

        patched_figure["data"][(i*3)+1]["y"] = [curve_std * diff_std, curve_std * diff_std]
        patched_figure["data"][(i*3)+2]["y"] = [-(curve_std * diff_std), -(curve_std * diff_std)]

        peaks_pos, _ = find_peaks(diff, height=curve_std * diff_std, threshold = 0)
        peaks_neg, _ = find_peaks(-diff, height=curve_std * diff_std, threshold = 0)

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

        intervals_all_pos.append(
            {
                "interval": merged_pos,
                "weight": (1 / dist**weight) / total_dist * 100,
                "curve": idx
            }
        )
        intervals_all_neg.append(
            {
                "interval": merged_neg,
                "weight": (1 / dist**weight) / total_dist * 100,
                "curve": idx
            }
        )

        for start, end in merged_pos:
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": datetime_str[int(start)],
                    "x1": datetime_str[int(end)],
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
                    "x0": datetime_str[int(start)],
                    "x1": datetime_str[int(end)],
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

    return patched_figure, all_peaks, number_of_segments, quantity_mean_std


@callback(
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Output("home_results_day_graph", "figure", allow_duplicate=True),
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
        (Output("home_load_data_btn", "disabled"), True, False),
        (Output("home_smooth_window_input", "disabled"), True, False),
        (Output("home_n_apply_smooth_input", "disabled"), True, False),
        (Output("home_apply_dtw_btn", "disabled"), True, False),
        (Output("home_diff_std_input", "disabled"), True, False),
        (Output("home_min_curves_input", "disabled"), True, False),
        (Output("home_number_of_segments_input", "disabled"), True, False),
        (Output("home_quantity_mean_std_input", "disabled"), True, False),
        (Output("home_dtw_weight_input", "disabled"), True, False),
        (Output("home_avoid_border_input", "disabled"), True, False),
        (Output("home_merge_gap_input", "disabled"), True, False),
        (Output("home_relative_height_input", "disabled"), True, False),
        (Output("home_get_results_btn", "disabled"), True, False),
        (Output("home_download_button", "disabled"), True, False),
        (Output("home_results_add_new_log_multiselect", "disabled"), True, False),
        (Output("home_results_add_new_log_btn", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def home_get_results(
    nc1: int,
    peaks_intervals: dict,
    loaded_data: dict,
    min_curves: int,
    dtw_data: dict,
    search: str,
) -> tuple[Patch, Patch, Patch, list, list[dict]]:
    """
    Function responsible for generating the results data and plotting into the graphs `home_results_graph` and
    `home_results_background_graph` and also displaying the logs of the peaks inside the `home_results_log` component.

    Parameters
    ----------
    nc1 : int
        Input for when get results button is clicked.

    peaks_intervals : dict
        A dict with the list of all positive and negative peaks::

            {
                "pos": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
                "neg": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
            }

    loaded_data : dict
        The loaded data of the curves::

            {
                "target": {
                    "data": list[float]
                        X-axis data of the target curve.
                    "table": np.recarray
                        The FITS table of the target curve.
                    "day": str
                        The day of the target curve.
                },
                "curves": {
                    "data_list": list[list[float]]
                        X-axis data of the curves to be compared.
                    "data_times": list[np.ndarray]
                        A list for the datetimes of the curves to be compared.
                    "days": list[str]
                        The day of each curve.
                }
            }

    min_curves : int
        Number of minimum curves to have a peak at that period in time.

    dtw_data : dict
        A dict to store the DTW obtained data::

            {
                "resultados": list[tuple[int, float]]
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

    Patch
        A patched figure to update the curves of the result day graph.

    list
        A list of logs of each estimated peak (Initial time - Final time).

    list[dict]
        A list of the dicts with the data of each possible flare stored in `home_events_data`::

            {
                "x": list[str]
                    List of the datetime strings of the target event.
                "y": list[float]
                    List of the intensity of the background subtraction of each event.
                "curves": list[int]
                    Indexes of curves used to take the median of this curve
            }
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
        translated = TRANSLATIONS["pt"]

    # --- Getting curve data ---

    smooth_window = dtw_data["smooth_window"]
    n_apply_smooth = dtw_data["n_apply_smooth"]
    
    target_data = loaded_data["target"]["data"]
    target_table = loaded_data["target"]["table"]
    target_day = loaded_data["target"]["day"]
    curve_data_list = loaded_data["curves"]["data_list"]
    curve_days = loaded_data["curves"]["days"]
    datetime_list, datetime_str = generate_datetime_list(target_table)

    common_pos = find_common_intervals_weighted(peaks_intervals["pos"], min_curves)
    common_neg = find_common_intervals_weighted(peaks_intervals["neg"], min_curves)

    # --- Results ---

    patched_figure = Patch()

    target_y = apply_smooth(target_data, smooth_window=smooth_window, n_apply_smooth=n_apply_smooth)

    # --- Background ---

    background_patched_figure = Patch()
    
    target_len = len(target_data)

    curves_raw_interp = [interpolate_curve(curve, target_len) for curve in curve_data_list]
    curves_raw_smooth = [apply_smooth(curve, smooth_window, n_apply_smooth) for curve in curves_raw_interp]

    # --- Getting logs ---

    shapes = []
    logs = []
    background_curves = []
    index = 0

    day_curve = np.zeros(len(datetime_str), dtype=float)

    for idx, ((start, end), curves) in enumerate(common_pos):
        curves_raw_smooth_array = np.stack(curves_raw_smooth)
        background_curve = np.median(curves_raw_smooth_array[curves, :], axis=0)
        background_subtracted = np.array(target_data) - np.array(background_curve)

        extra_time = len(datetime_str[int(start):int(end)])/2
        start_time = max(0, start - extra_time)
        end_time = min(len(datetime_str), end + extra_time)

        start_time_log = datetime_str[int(start)][11:]
        end_time_log = datetime_str[int(end)][11:]

        if not is_linear_curve(background_subtracted[int(start_time):int(end_time)]):
            logs.append(
                generate_new_log(translated, index, curve_days, start_time_log, end_time_log, True)
            )
            shapes.append(
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": datetime_str[int(start_time)],
                    "x1": datetime_str[int(end_time)],
                    "y0": 0,
                    "y1": 1,
                    "fillcolor": "#ffcb48",
                    "opacity": 0.3,
                    "line": {"width": 0},
                }
            )

            background_curves.append(
                {
                    "x": datetime_str[int(start_time):int(end_time)],
                    "y": background_subtracted[int(start_time):int(end_time)],
                    "curves": curves,
                }
            )

            day_curve[int(start_time):int(end_time)] = background_subtracted[int(start_time):int(end_time)]

            index += 1

    # --- Plot ---

    
    hover_template = "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"
    patched_figure["data"] = [
        go.Scatter(
            y=target_data,
            x=datetime_list,
            mode='lines',
            name=f"[{translated['graphs']['original']}] {target_day}",
            line=dict(width=1, color="#bdb4fc"),
            opacity=0.5,
            hovertemplate=hover_template,
        ),
        go.Scatter(
            y=target_y,
            x=datetime_list,
            mode='lines',
            name=f"[{translated['graphs']['smoothed']}] {target_day}",
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
                name=f"{target_day}",
                line=dict(width=2, color=BACKGROUND_LINE_COLOR),
                opacity=1,
                hovertemplate=hover_template,
            ),
        ]

    patched_figure["layout"]["shapes"] = shapes

    # --- Day plot ---

    day_patched_figure = Patch()

    day_patched_figure["data"] = [
        go.Scatter(
            y=day_curve,
            x=datetime_str,
            mode='lines',
            name=f"{target_day}",
            line=dict(width=2, color=BACKGROUND_LINE_COLOR),
            opacity=1,
            hovertemplate=hover_template,
        ),
    ]

    return patched_figure, background_patched_figure, day_patched_figure, logs, background_curves


@callback(
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Input({"type": "possible_flare", "index": ALL, "id": "home_event_display_btn"}, "n_clicks"),
    State("home_events_data", "data"),
    prevent_initial_call=True,
)
def home_load_possible_flare(nc1: list[int], events_data: list[dict]) -> Patch:
    """
    Function responsible for loading the event into the background graph `home_results_background_graph`
    when clicking on a possible flare in the logs.

    Parameters
    ----------
    nc1 : list[int]
        List of logs for when get one of them is clicked.

    events_data : list[dict]
        A list of the dicts with the data of each possible flare stored in `home_events_data`::

            {
                "x": list[str]
                    List of the datetime strings of the target event.
                "y": list[float]
                    List of the intensity of the background subtraction of each event.
                "curves": list[int]
                    Indexes of curves used to take the median of this curve
            }


    Returns
    -------
    Patch
        A patched figure to update the curve of the result background graph given a possible event.
    """
    try:
        if any(events_data):
            triggered_id = callback_context.triggered_id
            idx = int(triggered_id["index"])

            patched_figure = Patch()

            patched_figure["data"][0]["x"] = events_data[idx]["x"]
            patched_figure["data"][0]["y"] = events_data[idx]["y"]

            return patched_figure
        return no_update
    except:
        return no_update


@callback(
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Output("home_results_day_graph", "figure", allow_duplicate=True),
    Output("home_events_data", "data", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "className"),
    Input({"type": "possible_flare", "index": ALL, "id": "home_event_update_btn"}, "n_clicks"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "className"),
    State("home_events_data", "data"),
    State("home_graph_raw_data", "data"),
    State("home_peaks_intervals", "data"),
    State("home_min_curves_input", "value"),
    State("home_dtw_result_data", "data"),
    prevent_initial_call=True,
)
def home_update_flare_info(
    nc1: list[int],
    starts: list[str],
    ends: list[str],
    curve_select: list[int],
    offset: list[int],
    checkbox_classname: list[str],
    events_data: list[dict],
    loaded_data: dict,
    peaks_intervals: dict,
    min_curves: int,
    dtw_data: dict,
) -> tuple[Patch, Patch, Patch, list[dict], list[str]]:
    """
    Function responsible for updating the data of the flare.

    Parameters
    ----------
    nc1 : list[int]
        List of logs for when get one of them is clicked.

    starts : list[str]
        List of start values of all the events.

    ends : list[str]
        List of end values of all the events.

    curve_select : list[int]
        List of curve index to be used for background subtraction for all events.
    
    offset : list[int]
        List of offsets to be used for background subtraction for all events.

    checkbox_classname : list[str]
        List of classnames of the automatic checkbox of all events to check if it is automatic or not.

    events_data : list[dict]
        A list of the dicts with the data of each possible flare stored in `home_events_data`::

            {
                "x": list of datetime
                    List of the dates of the target event.
                "y": list of float
                    List of the intensity of the background subtraction of each event.
                "curves": list of int
                    Indexes of curves used to take the median of this curve
            }

    loaded_data : dict
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
                    "data_times": list of Datetimes
                        A list for the datetimes of the curves to be compared.
                    "days": list ofstr
                        The day of each curve.
                }
            }

    peaks_intervals : dict
        A dict with the list of all positive and negative peaks::

            {
                "pos": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
                "neg": dict
                    - "interval": list of tuples [(start, end), ...]
                    - "weight": float, weight of this interval (0-100)
                    - "curve": any, identifier of the curve
            }

    min_curves : int
        Number of minimum curves to have a peak at that period in time.

    dtw_data : dict
        A dict to store the DTW obtained data::

            {
                "resultados": list of tuple[int, float]
                    List of each index and distance of each curve to the target.
                "smooth_window": int
                    Number of neighbours used to apply the smoothing.
                "n_apply_smooth": int
                    Number of iterations to apply the smoothing with `smooth_window` neighbours.
            }


    Returns
    -------
    tuple[Patch, Patch, Patch, list[dict], list[str]]
        If a flare is updated, returns:
            - results_patched_figure: Patch for the results graph
            - background_patched_figure: Patch for the background graph
            - day_patched_figure: Patch for the day graph
            - events_data: Updated events data
            - checkbox_classname: Updated checkbox classnames

        If an error occurs or no update is needed, returns multiple `no_update` values.
    """
    try:
        if any(events_data) and any(nc1):
            triggered_id = callback_context.triggered_id
            idx = int(triggered_id["index"])

            checkbox_classname[idx] = "logs-checkbox-changed"

            results_patched_figure = Patch()

            target_day = loaded_data["target"]["day"]
            target_data = loaded_data["target"]["data"]
            target_table = loaded_data["target"]["table"]
            target_datetime_list, target_datetime_str = generate_datetime_list(target_table)

            results_patched_figure["layout"]["shapes"][idx]["x0"] = f"{target_day} {starts[idx]}"
            results_patched_figure["layout"]["shapes"][idx]["x1"] = f"{target_day} {ends[idx]}"

            if int(curve_select[idx]) < 6:
                curve_data = loaded_data["curves"]["data_list"][int(curve_select[idx])]
                curve_datetime_list = loaded_data["curves"]["data_times"][int(curve_select[idx])]

                curve_aligned = interpolate_curve_to_target_time(
                    target_datetime_list,
                    curve_datetime_list,
                    curve_data
                )

                background_subtracted = np.array(target_data) - np.array(curve_aligned)
            else:
                curve_data_list = loaded_data["curves"]["data_list"]

                smooth_window = dtw_data["smooth_window"]
                n_apply_smooth = dtw_data["n_apply_smooth"]

                target_len = len(target_data)

                curves = events_data[idx]["curves"]

                curves_raw_interp = [interpolate_curve(curve, target_len) for curve in curve_data_list]
                curves_raw_smooth = [apply_smooth(curve, smooth_window, n_apply_smooth) for curve in curves_raw_interp]
                
                curves_raw_smooth_array = np.stack(curves_raw_smooth)
                background_curve = np.median(curves_raw_smooth_array[curves, :], axis=0)
                background_subtracted = np.array(target_data) - np.array(background_curve)

            # original strings
            start = f"{target_day} {starts[idx]}"
            end = f"{target_day} {ends[idx]}"

            # format
            fmt = "%Y-%m-%d %H:%M:%S"

            # convert to datetime
            start_dt = datetime.strptime(start, fmt)
            end_dt = datetime.strptime(end, fmt)

            # difference in seconds
            extra_time = int((end_dt - start_dt).total_seconds() / 2)

            # expand window
            new_start_dt = start_dt - timedelta(seconds=extra_time)
            new_end_dt = end_dt + timedelta(seconds=extra_time)

            # convert back to string
            new_start = new_start_dt.strftime(fmt)
            new_end = new_end_dt.strftime(fmt)

            start_idx = get_closest_datetime_index(
                target_datetime_list,
                new_start,
            )

            end_idx = get_closest_datetime_index(
                target_datetime_list,
                new_end,
            )

            events_data[idx]["x"] = target_datetime_str[int(start_idx):int(end_idx)]
            events_data[idx]["y"] = background_subtracted[int(start_idx):int(end_idx)] - offset[idx]

            background_patched_figure = Patch()

            background_patched_figure["data"][0]["x"] = events_data[idx]["x"]
            background_patched_figure["data"][0]["y"] = events_data[idx]["y"]

            day_curve = np.zeros(len(target_datetime_str), dtype=float)

            # Criar mapeamento tempo → índice (muito mais eficiente que .index())
            time_to_index = {t: i for i, t in enumerate(target_datetime_str)}

            for event in events_data:
                x_vals = event["x"]
                y_vals = event["y"]

                # Pegar índices correspondentes
                indices = [time_to_index[t] for t in x_vals]

                # Atribuir valores
                day_curve[indices] = y_vals

            day_patched_figure = Patch()

            day_patched_figure["data"][0]["y"] = day_curve

            return results_patched_figure, background_patched_figure, day_patched_figure, events_data, checkbox_classname
        return no_update
    except:
        return no_update


@callback(
    Output("home_results_log", "children", allow_duplicate=True),
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output("home_events_data", "data", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "checked", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_is_valid"}, "checked", allow_duplicate=True),
    Input({"type": "possible_flare", "index": ALL, "id": "home_event_delete_btn"}, "n_clicks"),
    State("home_events_data", "data"),
    State("home_results_log", "children"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "checked"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_valid"}, "checked"),
    prevent_initial_call=True,
)
def home_delete_flare_from_log(
    nc1: list[int],
    events_data: list[dict],
    results_log: list,
    starts: list[str],
    ends: list[str],
    curve_select: list[int],
    offset: list[int],
    checked: list[bool],
    checked_valid: list[bool],
) -> tuple[list, Patch, list[dict], list[str], list[str], list[int], list[int], list[bool]]:
    """
    Delete a possible flare entry from the results log and update
    all associated UI state and stored data.

    This callback is triggered when any dynamic delete button
    (pattern-matching component with type="possible_flare")
    is clicked.

    When triggered, the function:

        1. Identifies which flare entry initiated the callback.
        2. Removes the corresponding rectangular shape from the
        results graph using a Patch object.
        3. Removes the corresponding entry from `events_data`.
        4. Reorders the UI state lists (`starts`, `ends`,
        `curve_select`, `offset`) by moving the deleted index
        to the end (to preserve index consistency).
        5. Removes the last visual log component from `results_log`.

    If no button was clicked, the callback returns `no_update`.

    Parameters
    ----------
    nc1 : list[int]
        List containing the number of clicks for each dynamic
        delete button. The triggered index determines which
        flare entry will be removed.

    events_data : list[dict]
        Stored flare metadata from `home_events_data`, where
        each entry has the format::

            {
                "x": list of str
                    Datetime strings defining the flare interval.
                "y": list of float
                    Background-subtracted intensity values.
                "curves": list of int
                    Indexes of curves used for background subtraction.
            }

    results_log : list
        Current list of UI components stored in
        `home_results_log.children`.

    starts : list[str]
        List of start time values for all flare entries.

    ends : list[str]
        List of end time values for all flare entries.

    curve_select : list[int]
        List of selected curve indices used for background subtraction
        for each flare entry.

    offset : list[int]
        List of offset values used for background subtraction
        for each flare entry.

    checked : list[bool]
        List of checkboxes for knowing if event was automatically detected
        or not.

    checked_valid : list[bool]
        List of checkboxes for knowing if event was marked as valid

    Returns
    -------
    tuple[list, Patch, list[dict], list[str], list[str], list[int], list[int], list[bool]]

        If a delete action is triggered, returns:

            - Updated `results_log`
            - A patched figure with the corresponding shape removed
            - Updated `events_data`
            - Updated `starts`
            - Updated `ends`
            - Updated `curve_select`
            - Updated `offset`
            - Updated `checked`

        If no delete action occurs or an exception is raised,
        returns multiple `no_update` values.
    """
    try:
        if any(nc1):
            triggered_id = callback_context.triggered_id
            idx = int(triggered_id["index"])

            results_patched_figure = Patch()

            del results_patched_figure["layout"]["shapes"][idx]

            events_data.pop(idx)

            item = starts.pop(idx)
            starts.append(item)

            item = ends.pop(idx)
            ends.append(item)

            item = curve_select.pop(idx)
            curve_select.append(item)

            item = offset.pop(idx)
            offset.append(item)

            item = checked.pop(idx)
            checked.append(item)

            item = checked_valid.pop(idx)
            checked_valid.append(item)

            results_log.pop(-1)

            return results_log, results_patched_figure, events_data, starts, ends, curve_select, offset, checked, checked_valid
        return no_update
    except:
        return no_update


@callback(
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value"),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value"),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value"),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value"),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "checked"),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_is_valid"}, "checked"),
    Output("home_events_data", "data", allow_duplicate=True),
    Input({"type": "possible_flare", "index": ALL, "id": "home_log_move_up_btn"}, "n_clicks"),
    Input({"type": "possible_flare", "index": ALL, "id": "home_log_move_down_btn"}, "n_clicks"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "checked"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_valid"}, "checked"),
    State("home_events_data", "data"),
    State("home_results_graph", "figure"),
    prevent_initial_call=True,
)
def home_move_flare_info(
    nc1: list[int],
    nc2: list[int],
    starts: list[str],
    ends: list[str],
    curve_select: list[int],
    offset: list[int],
    checked: list[bool],
    checked_valid: list[bool],
    events_data: list[dict],
    fig: dict,
) -> tuple[Patch, list[str], list[str], list[int], list[int], list[bool], list[dict]]:
    """
    Reorders the flare events when the user clicks the "move up" or "move down" buttons.

    This callback swaps the position of a selected event with the previous or next
    event in the list, updating all related state values accordingly.

    Parameters
    ----------
    nc1 : list[int]
        List of click counts for all "move up" buttons.

    nc2 : list[int]
        List of click counts for all "move down" buttons.

    starts : list[str]
        List of start time values for all flare events.

    ends : list[str]
        List of end time values for all flare events.

    curve_select : list[int]
        List of selected curve indices used for background subtraction
        for each flare event.

    offset : list[int]
        List of offset values used for background subtraction
        for each flare event.

    checked : list[bool]
        List of checkboxes for knowing if event was automatically detected
        or not.

    checked_valid : list[bool]
        List of checkboxes for knowing if event was marked as valid

    events_data : list[dict]
        List containing the stored data for each flare event. Each item has
        the following structure::

            {
                "x": list[str]
                    Datetime strings of the event.
                "y": list[float]
                    Background-subtracted intensity values.
                "curves": list[int]
                    Indices of curves used to compute the median.
            }

    fig : dict
        Dictionary representation of the figure from the Results graph.

    Returns
    -------
    tuple[Patch, list[str], list[str], list[int], list[int], list[bool], list[dict]]
        Updated lists with reordered values if a move action is triggered.
        Returns multiple `no_update` values if no valid move operation is performed.
    """
    try:
        triggered_id = callback_context.triggered_id
        if any(events_data) and (any(nc1) or any(nc2)):
            triggered_id = callback_context.triggered_id
            idx = int(triggered_id["index"])
            type = triggered_id["id"]

            if type == "home_log_move_up_btn":
                if idx == 0:
                    return no_update

                starts[idx], starts[idx-1] = starts[idx-1], starts[idx]
                ends[idx], ends[idx-1] = ends[idx-1], ends[idx]
                curve_select[idx], curve_select[idx-1] = curve_select[idx-1], curve_select[idx]
                offset[idx], offset[idx-1] = offset[idx-1], offset[idx]
                checked[idx], checked[idx-1] = checked[idx-1], checked[idx]
                checked_valid[idx], checked_valid[idx-1] = checked_valid[idx-1], checked_valid[idx]
                events_data[idx], events_data[idx-1] = events_data[idx-1], events_data[idx]

                patched_figure = Patch()

                (
                    patched_figure["layout"]["shapes"][idx],
                    patched_figure["layout"]["shapes"][idx - 1],
                ) = (
                    fig["layout"]["shapes"][idx - 1],
                    fig["layout"]["shapes"][idx],
                )

                return patched_figure, starts, ends, curve_select, offset, checked, checked_valid, events_data
            elif type == "home_log_move_down_btn":
                if idx == (len(starts) - 1):
                    return no_update

                starts[idx], starts[idx+1] = starts[idx+1], starts[idx]
                ends[idx], ends[idx+1] = ends[idx+1], ends[idx]
                curve_select[idx], curve_select[idx+1] = curve_select[idx+1], curve_select[idx]
                offset[idx], offset[idx+1] = offset[idx+1], offset[idx]
                checked[idx], checked[idx+1] = checked[idx+1], checked[idx]
                checked_valid[idx], checked_valid[idx+1] = checked_valid[idx+1], checked_valid[idx]
                events_data[idx], events_data[idx+1] = events_data[idx+1], events_data[idx]
                
                patched_figure = Patch()

                (
                    patched_figure["layout"]["shapes"][idx],
                    patched_figure["layout"]["shapes"][idx + 1],
                ) = (
                    fig["layout"]["shapes"][idx + 1],
                    fig["layout"]["shapes"][idx],
                )

                return patched_figure, starts, ends, curve_select, offset, checked, checked_valid, events_data
        return no_update
    except:
        return no_update


@callback(
    Output("home_results_log", "children", allow_duplicate=True),
    Output("home_results_graph", "figure", allow_duplicate=True),
    Output("home_events_data", "data", allow_duplicate=True),
    Output({"type": "possible_flare", "index": ALL, "id": "home_event_delete_btn"}, "n_clicks"),
    Input("home_results_add_new_log_btn", "n_clicks"),
    State("home_results_log", "children"),
    State("home_results_add_new_log_multiselect", "value"),
    State("home_results_add_new_log_multiselect", "data"),
    State("home_events_data", "data"),
    State("home_graph_raw_data", "data"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_delete_btn"}, "n_clicks"),
    State("url", "search"),
    prevent_initial_call=True,
)
def home_generate_new_event_log(
    nc1: int,
    logs: list,
    curve_days_index: list[str],
    curve_days_data: list[dict],
    events_data: list[dict],
    loaded_data: dict,
    nc_reset: list[int],
    search: str,
) -> tuple[list, Patch, list[dict], list[int]]:
    """
    Create a new event log entry, update the results graph, and reset
    dynamic delete buttons.

    This callback is triggered when the "add new log" button is clicked.
    It appends a new log block to the UI, adds a visual time interval
    (rectangular shape) to the results graph, updates the stored
    events metadata, and resets all delete-button click counters.

    Parameters
    ----------
    nc1 : int
        Number of clicks on the "add new log" button.

    logs : list
        Current list of log UI components stored in
        "home_results_log.children".

    curve_days_index : list[str]
        List of selected curve indexes from the MultiSelect component.
        Each element corresponds to the "value" field of the available
        curve options and is converted to int before storage.

    curve_days_data : list[dict]
        Available curve options from the MultiSelect component.
        Each element has the format::

            {
                "value": str,
                "label": str
            }

    events_data : list[dict]
        Stored list of event metadata. Each event is represented as::

            {
                "x": list[str]
                    Datetime strings defining the event interval.
                "y": list[float]
                    Background-subtracted intensity values.
                "curves": list[int]
                    Indexes of curves used to compute the median
                    associated with this event.
            }

    loaded_data : dict
        Dictionary containing the loaded curve data::

            {
                "target": {
                    "data": list[float]
                        Intensity values of the target curve.
                    "table": FITS_rec
                        FITS table of the target curve.
                    "day": str
                        Day string of the target curve (YYYY-MM-DD).
                },
                "curves": {
                    "data_list": list[list[float]]
                        Intensity values of comparison curves.
                    "data_times": list[list[float]]
                        Datetime arrays (as timestamps) for each comparison curve.
                    "days": list[str]
                        Day string of each comparison curve.
                }
            }

    nc_reset : list[int]
        Current click counters of all dynamic delete buttons
        (pattern-matching component with ALL index).

    search : str
        URL query string used to determine the page language.

    Returns
    -------
    tuple[list, Patch, list[dict], list[int]]
        logs : list
            Updated list of log UI components including the newly
            created event log.

        patched_figure : Patch
            Patch object that appends a rectangular shape to the
            results graph representing the new event time interval.

        events_data : list[dict]
            Updated list of stored event metadata including the
            newly created event.

        nc_reset : list[int]
            Reset click counters for all dynamic delete buttons
            (set to None to prevent unintended repeated triggers).
    """
    # --- Getting language of the page ---

    query_params = parse_qs(search.lstrip("?"))  # remove "?" and parse
    lang = query_params.get("lang", ["not recognized"])[0]
    try:
        translated = TRANSLATIONS[lang]
    except:
        lang = "pt"
        translated = TRANSLATIONS["pt"]

    index = len(logs)

    start_time_log = "12:00:00"
    end_time_log = "12:00:00"

    curve_days = [curve_data["label"] for curve_data in curve_days_data]

    logs.append(
        generate_new_log(translated, index, curve_days, start_time_log, end_time_log, False)
    )

    target_day = loaded_data["target"]["day"]

    patched_figure = Patch()

    patched_figure["layout"]["shapes"].append(
        {
            "type": "rect",
            "xref": "x",
            "yref": "paper",
            "x0": f"{target_day} {start_time_log}",
            "x1": f"{target_day} {end_time_log}",
            "y0": 0,
            "y1": 1,
            "fillcolor": "#ffcb48",
            "opacity": 0.3,
            "line": {"width": 0},
        }
    )

    events_data.append(
        {
            "x": [f"{target_day} {start_time_log}"],
            "y": [0],
            "curves": [int(curve_idx) for curve_idx in curve_days_index]
        }
    )

    nc_reset = [None for _ in nc_reset]

    return logs, patched_figure, events_data, nc_reset


@callback(
    Output("home_results_background_graph", "figure", allow_duplicate=True),
    Output("home_results_day_graph", "figure", allow_duplicate=True),
    Input("home_results_tabs", "value"),
    prevent_initial_call=True,
)
def home_force_relayout_on_tab(tab: str) -> tuple:
    """
    Force the relayout of the background and day result graphs when switching tabs to ensure proper rendering and responsiveness.

    This callback is triggered whenever the user switches between the "background" and "day" tabs in the results section.
    It updates the `uirevision` property of the corresponding graph's layout, forcing Plotly to recalculate the graph size
    and layout, which resolves issues with responsiveness when the graph is initially hidden.

    Parameters
    ----------
    tab : str
        The value of the currently selected tab in the results section.
        Possible values are:
            - "result"
            - "background"
            - "day"

    Returns
    -------
    tuple[Patch | dash.no_update, Patch | dash.no_update]
        patched_figure : Patch or dash.no_update
            Patch object with an updated `uirevision` for the graph corresponding to the selected tab,
            or `no_update` if the tab is not active.

        patched_figure : Patch or dash.no_update
            Patch object with an updated `uirevision` for the other graph, or `no_update` if not applicable.
    """
    if tab == "background":
        patched_figure = Patch()
        patched_figure["layout"]["uirevision"] = str(np.random.rand())
        return patched_figure, no_update
    elif tab == "day":
        patched_figure = Patch()
        patched_figure["layout"]["uirevision"] = str(np.random.rand())
        return no_update, patched_figure
    return no_update, no_update


@callback(
    Input("home_download_button", "n_clicks"),
    State("home_download_extension_select", "value"),
    
    State({"type": "possible_flare", "index": ALL, "id": "home_event_start_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_end_time"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_curve_select"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_offset"}, "value"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "checked"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_automatic"}, "className"),
    State({"type": "possible_flare", "index": ALL, "id": "home_event_is_valid"}, "checked"),

    State("home_date_input", "value"),
    State("home_data_select", "value"),
    State("home_interpolation_select", "value"),
    State("home_smooth_window_input", "value"),
    State("home_n_apply_smooth_input", "value"),
    State("home_diff_std_input", "value"),
    State("home_number_of_segments_input", "value"),
    State("home_quantity_mean_std_input", "value"),
    State("home_merge_gap_input", "value"),
    State("home_relative_height_input", "value"),
    State("home_avoid_border_input", "value"),
    State("home_min_curves_input", "value"),
    State("home_dtw_weight_input", "value"),
    State("home_events_data", "data"),
    prevent_initial_call=True,
)
def home_download_results(
    n_clicks: int,
    extension: str,

    start_times: list[str],
    end_times: list[str],
    curve_select: list[int],
    offsets: list[int],
    is_automatic: list[bool],
    is_edited: list[str],
    checked_valid: list[bool],

    date: str,
    data_select: str,
    interpolation_select: str,
    smooth_window: int,
    n_apply_smooth: int,
    diff_std: float,
    number_of_segments: int,
    quantity_mean_std: int,
    merge_gap: int,
    relative_height: float,
    avoid_border: float,
    min_curves: int,
    dtw_weight: float,
    events_data: list[dict],
) -> None:
    """
    Callback responsible for handling the download of results in the selected format.

    Parameters
    ----------
    n_clicks : int
        Number of clicks on the download button.

    extension : str
        The selected file extension for download.

    start_times : list[str]
        List of start time values for all flare events.

    end_times : list[str]
        List of end time values for all flare events.

    curve_select : list[int]
        List of selected curve indices used for background subtraction for each flare event.

    offsets : list[int]
        List of offset values used for background subtraction for each flare event.

    is_automatic : list[bool]
        List of checkboxes for knowing if event was automatically detected or not.

    is_edited : list[str]
        List of classnames of the automatic checkbox of all events to check if it was edited or not.

    checked_valid : list[bool]
        List of checkboxes for knowing if event was marked as valid.

    date : str
        The date of the curve to be analyzed (YYYY-MM-DD format).

    data_select : str
        The position of the curve to be loaded in the fits file.

    interpolation_select : str
        The type of interpolation to be applied to the curves.

    smooth_window : int
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    diff_std : float
        The multiplier of the standard deviation to be used to find peaks.

    number_of_segments : int
        Number of segments that the curve will be divided for analysing.

    quantity_mean_std : int
        Number of stds selected from segments to take the mean.

    merge_gap : int
        The distance of points to merge peaks if they are too close to each other.

    relative_height : float
        The % of height used to find peaks.

    avoid_border : float
        Value to not consider border (0 - 30)%.

    min_curves : int
        Number of minimum curves to have a peak at that period in time.

    dtw_weight : float
        The weight for the DTW distances.

    events_data : list[dict]
        A list of the dicts with the data of each possible flare stored in `home_events_data`::
            {
                "x": list[str]
                    List of the datetime strings of the target event.
                "y": list[float]
                    List of the intensity of the background subtraction of each event.
                "curves": list[int]
                    Indexes of curves used to take the median of this curve
            }

    Returns
    -------
    None
    """
    if extension == "temp":
        save_event_times_to_json(date, start_times, end_times)
        return
    elif extension == "db":
        data_to_save = {
            date: {
                "input_data": {
                    "data_select": data_select,
                    "interpolation_select": interpolation_select,
                    "smooth_window": smooth_window,
                    "n_apply_smooth": n_apply_smooth,
                    "diff_std": diff_std,
                    "number_of_segments": number_of_segments,
                    "quantity_mean_std": quantity_mean_std,
                    "merge_gap": merge_gap,
                    "relative_height": relative_height,
                    "avoid_border": avoid_border,
                    "min_curves": min_curves,
                    "dtw_weight": dtw_weight
                },
                "event_data": [
                    {
                        "metadata": {
                            "start_time": start_time,
                            "end_time": end_time,
                            "curve_select": curve_idx,
                            "offset": offset,
                            "is_automatic": is_auto,
                            "is_edited": bool(is_edit == "logs-checkbox-changed"),
                            "is_valid": is_valid
                        },
                        "numeric_data": {
                            **events_data[idx]
                        }
                    }
                    for idx, (start_time, end_time, curve_idx, offset, is_auto, is_edit, is_valid) in enumerate(zip(
                        start_times, end_times, curve_select, offsets, is_automatic, is_edited, checked_valid
                    ))
                ]
            }
        }
        save_event_times_to_db(data_to_save)
        return