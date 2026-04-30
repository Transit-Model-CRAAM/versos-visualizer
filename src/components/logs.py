from dash import html, Output, Input, State, Patch
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def generate_new_log(translated: dict, index: int, curve_days: list[str], start_time: str, end_time: str, checked: bool):
    curve_data = [
        {"label": curve_day, "value": f"{curve_idx}"}
        for curve_idx, curve_day in enumerate(curve_days)
    ]

    curve_data.append({
        "label": translated["logs"]["median"],
        "value": f"{len(curve_days)}"
    })

    return dbc.ListGroupItem(
        children=[
            html.Div(
                [
                    dmc.ActionIcon(
                        [
                            DashIconify(
                                icon="mdi:menu-up",
                                color="#FFFFFF",
                            )
                        ],
                        className="home-results-move-btn button-style",
                        id={"type": "possible_flare", "index": index, "id": "home_log_move_up_btn"}
                    ),
                    dmc.ActionIcon(
                        [
                            DashIconify(
                                icon="mdi:menu-down",
                                color="#FFFFFF",
                            )
                        ],
                        className="home-results-move-btn button-style",
                        id={"type": "possible_flare", "index": index, "id": "home_log_move_down_btn"}
                    ),
                ],
                className="home-move-buttons-container",
            ),
            dmc.TimePicker(
                label=translated["logs"]["start"],
                value=start_time,
                withSeconds=True,
                format="24h",
                id={"type": "possible_flare", "index": index, "id": "home_event_start_time"}
            ),
            dmc.TimePicker(
                label=translated["logs"]["end"],
                value=end_time,
                withSeconds=True,
                format="24h",
                id={"type": "possible_flare", "index": index, "id": "home_event_end_time"}
            ),
            dmc.Select(
                label=translated["logs"]["curve"],
                value=f"{len(curve_days)}",
                data=curve_data,
                comboboxProps={"position": "top", "middlewares": {"flip": False, "shift": False}},
                id={"type": "possible_flare", "index": index, "id": "home_event_curve_select"},
                className="logs-curve"
            ),
            dmc.NumberInput(
                label=translated["logs"]["offset"],
                value=0,
                id={"type": "possible_flare", "index": index, "id": "home_event_offset"},
                className="logs-offset"
            ),
            html.Div(
                [
                    dmc.Checkbox(
                        disabled=True,
                        checked=checked,
                        id={"type": "possible_flare", "index": index, "id": "home_event_is_automatic"},
                        className="logs-checkbox"
                    ),
                    dmc.Checkbox(
                        checked=True,
                        id={"type": "possible_flare", "index": index, "id": "home_event_is_valid"},
                        className="logs-checkbox-valid"
                    ),
                ],
                className="logs-checkboxes-container",
            ),
            dmc.ActionIcon(
                [
                    DashIconify(
                        icon="mdi:graph-line",
                        color="#FFFFFF",
                    )
                ],
                className="home-results-btn button-style",
                id={"type": "possible_flare", "index": index, "id": "home_event_display_btn"}
            ),
            dmc.ActionIcon(
                [
                    DashIconify(
                        icon="mdi:reload",
                        color="#FFFFFF",
                    )
                ],
                className="home-results-btn button-style",
                id={"type": "possible_flare", "index": index, "id": "home_event_update_btn"}
            ),
            dmc.ActionIcon(
                [
                    DashIconify(
                        icon="mdi:trash",
                        color="#FFFFFF",
                    )
                ],
                className="home-results-btn button-style",
                id={"type": "possible_flare", "index": index, "id": "home_event_delete_btn"}
            )
        ],
        id={"type": "possible_flare", "index": index},
        className="home-results-log-up"
    )