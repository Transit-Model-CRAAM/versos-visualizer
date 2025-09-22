from src.constants.translations import TRANSLATIONS

PLOT_CONFIG = {
    "displaylogo": False,
    "displayModeBar": True,
    "scrollZoom": True,
    "responsive": True,
    "toImageButtonOptions": {
        "format": "png",
    },
}

BACKGROUND_LINE_COLOR = "#1980A0"
BACKGROUND_STD_LINE_COLOR = "orange"

COLORWAY = [
    "#0072B2",  # Strong blue
    "#009E73",  # Green
    "#E69F00",  # Orange
    "#56B4E9",  # Sky blue
    "#F0E442",  # Yellow (still visible on white)
    "#CC79A7",  # Purple
    "#E41A1C",  # Main vivid red (highlight)
]

def generate_plot_layout(lang: str) -> dict:
    """
    Function responsible for generating the regular plot layout

    Parameters
    ----------
    lang : str
        Language of the page ("pt" or "en").

    Returns
    -------
    dict
        The dict for the regular plot layout
    """
    translated = TRANSLATIONS[lang]
    return {
        "margin": {"r": 35, "t": 35, "b": 55, "l": 55},
        "legend": {
            "orientation": "h",  # horizontal legend
            "yanchor": "bottom",
            "y": -0.2,  # position below the graph
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "rgba(0,0,0,0)",  # transparent background
            "borderwidth": 0,
        },
        "yaxis": {"title": f"{translated['graphs']['intensity']} ({translated['graphs']['normalized']})"},
        "colorway": COLORWAY,
    }

def generate_fig_properties(lang: str) -> dict:
    """
    Function responsible for generating the regular fig properties

    Parameters
    ----------
    lang : str
        Language of the page ("pt" or "en").

    Returns
    -------
    dict
        The dict for the regular fig properties
    """
    return {
        "data": [],
        "layout": generate_plot_layout(lang),
    }

def generate_background_plot_layout(lang: str) -> dict:
    """
    Function responsible for generating the background plot layout

    Parameters
    ----------
    lang : str
        Language of the page ("pt" or "en").

    Returns
    -------
    dict
        The dict for the background plot layout
    """
    translated = TRANSLATIONS[lang]
    return {
        "margin": {"r": 35, "t": 35, "b": 55, "l": 55},
        "legend": {
            "orientation": "h",  # horizontal legend
            "yanchor": "bottom",
            "y": -0.2,  # position below the graph
            "xanchor": "center",
            "x": 0.5,
        },
        "xaxis": {
            "anchor": "y",
            "domain": [0, 1],
            "matches": "x",
            "showticklabels": False,
        },
        "xaxis2": {
            "anchor": "y2",
            "domain": [0, 1],
            "matches": "x",
            "showticklabels": False,
        },
        "xaxis3": {
            "anchor": "y3",
            "domain": [0, 1],
            "matches": "x",
            "showticklabels": False,
        },
        "xaxis4": {
            "anchor": "y4",
            "domain": [0, 1],
            "matches": "x",
            "showticklabels": False,
        },
        "xaxis5": {
            "anchor": "y5",
            "domain": [0, 1],
            "matches": "x",
            "showticklabels": False,
        },
        "xaxis6": {
            "anchor": "y6",
            "domain": [0, 1],
            "matches": "x",
            "title": {"text": f"{translated['graphs']['time']}"},
        },
        "yaxis": {
            "anchor": "x",
            "domain": [0.85, 1],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
        "yaxis2": {
            "anchor": "x2",
            "domain": [0.68, 0.84],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
        "yaxis3": {
            "anchor": "x3",
            "domain": [0.51, 0.67],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
        "yaxis4": {
            "anchor": "x4",
            "domain": [0.34, 0.5],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
        "yaxis5": {
            "anchor": "x5",
            "domain": [0.17, 0.33],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
        "yaxis6": {
            "anchor": "x6",
            "domain": [0, 0.16],
            "title": {"text": f"{translated['graphs']['intensity']}"},
        },
    }

def generate_background_fig_properties(lang: str) -> dict:
    """
    Function responsible for generating the background fig properties

    Parameters
    ----------
    lang : str
        Language of the page ("pt" or "en").

    Returns
    -------
    dict
        The dict for the background fig properties
    """
    translated = TRANSLATIONS[lang]
    hover_template = f"{translated['graphs']['point']} " + "%{x}<br>" + f"{translated['graphs']['intensity']}:" + " %{y:.4f}<extra></extra>"
    return {
        "data": [
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x",
                "y": [None],
                "yaxis": "y",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                "hovertemplate": hover_template,
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x",
                "yaxis": "y",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x",
                "yaxis": "y",
            },
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x2",
                "y": [None],
                "yaxis": "y2",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                'hovertemplate': hover_template
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x2",
                "yaxis": "y2",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x2",
                "yaxis": "y2",
            },
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x3",
                "y": [None],
                "yaxis": "y3",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                'hovertemplate': hover_template
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x3",
                "yaxis": "y3",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x3",
                "yaxis": "y3",
            },
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x4",
                "y": [None],
                "yaxis": "y4",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                'hovertemplate': hover_template
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x4",
                "yaxis": "y4",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x4",
                "yaxis": "y4",
            },
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x5",
                "y": [None],
                "yaxis": "y5",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                'hovertemplate': hover_template
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x5",
                "yaxis": "y5",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x5",
                "yaxis": "y5",
            },
            {
                "mode": "lines",
                "showlegend": False,
                "type": "scatter",
                "xaxis": "x6",
                "y": [None],
                "yaxis": "y6",
                "line": {"width": 1, "color": BACKGROUND_LINE_COLOR},
                'hovertemplate': hover_template
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x6",
                "yaxis": "y6",
            },
            {
                "type": "scatter",
                "mode": "lines",
                "y": [0, 0],
                "line": {"color": BACKGROUND_STD_LINE_COLOR, "width": 1, "dash": "dash"},
                "showlegend": False,
                "xaxis": "x6",
                "yaxis": "y6",
            },
        ],
        "layout": generate_background_plot_layout(lang),
    }
