import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from flask import Flask
from dash import Dash, dcc, html, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc

from countries_data import countries_data  # external file with your country list

###############################################################################
# 1) DATAFRAME
###############################################################################
df = pd.DataFrame(countries_data)

###############################################################################
# 2) PLOTLY SCOPE MAPPING
###############################################################################
scope_map = {
    "Europa":              "europe",
    "Asien":               "asia",
    "Afrika":              "africa",
    "Nordamerika":         "north america",
    "Südamerika":          "south america",
    "Austrálie/Oceánie":   "world",
    "Alle":                "world"
}

###############################################################################
# 3) MICRO-COUNTRIES COORDINATES (for very small states)
###############################################################################
micro_coords = {
    "Andorra": {"lat": 42.5063, "lon": 1.5218},
    "Malta": {"lat": 35.9375, "lon": 14.3754},
    "Monaco": {"lat": 43.7384, "lon": 7.4246},
    "San Marino": {"lat": 43.9424, "lon": 12.4578},
    "Vatikanstadt": {"lat": 41.9029, "lon": 12.4534},
}

###############################################################################
# 4) FLASK + DASH (with Bootstrap theme)
###############################################################################
flask_app = Flask(__name__)
app = Dash(__name__, server=flask_app, external_stylesheets=[dbc.themes.COSMO])

###############################################################################
# 5) LAYOUT: 3 SCREENS + STORES FOR QUIZ STATE
###############################################################################
app.layout = dbc.Container([
    # Stores for app state
    dcc.Store(id="store-current-screen", data=1),         # 1=Welcome, 2=Continent, 3=Quiz
    dcc.Store(id="store-chosen-continent", data=None),
    dcc.Store(id="store-selected-country", data=None),
    dcc.Store(id="store-correct-count", data=0),
    dcc.Store(id="store-wrong-count", data=0),
    dcc.Store(id="store-done-countries", data=[]),
    dcc.Store(id="store-remaining-countries", data=[]),

    # Navbar
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Länder-Ratespiel (Blindkarte)", className="ms-2")
        ]),
        color="dark", dark=True, className="mb-4"
    ),

    # SCREEN 1: Welcome
    dbc.Card(
        [
            dbc.CardHeader("Willkommen"),
            dbc.CardBody([
                html.H4("Mina & Valentina – Herzlich willkommen!", className="card-title", style={"textAlign": "center"}),
                html.P("Kleines Länder-Ratespiel auf einer Blindkarte.", className="card-text", style={"textAlign": "center"}),
                dbc.Button("Weiter", id="btn-to-screen-2", n_clicks=0, color="primary", className="d-block mx-auto mt-3")
            ])
        ],
        id="screen-1",
        style={"maxWidth": "600px", "margin": "0 auto 2rem auto"}
    ),

    # SCREEN 2: Continent Selection
    dbc.Card(
        [
            dbc.CardHeader("Kontinent auswählen"),
            dbc.CardBody([
                dcc.Dropdown(
                    id="continent-dropdown",
                    options=[{"label": "Alle", "value": "Alle"}] + [
                        {"label": c, "value": c} for c in sorted(df["continent"].unique())
                    ],
                    placeholder="Kontinent auswählen...",
                    style={"width": "100%", "maxWidth": "300px", "marginBottom": "20px"}
                ),
                dbc.Button("Spiel starten", id="btn-to-screen-3", n_clicks=0, color="success")
            ])
        ],
        id="screen-2",
        style={"display": "none", "maxWidth": "600px", "margin": "0 auto 2rem auto"}
    ),

    # SCREEN 3: Quiz
    dbc.Card(
        [
            dbc.CardHeader("Quiz"),
            dbc.CardBody([
                html.Div([
                    html.Label("Welches Land ist rot markiert?", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="country-guess-dropdown", style={"width": "100%", "maxWidth": "300px"}),
                    dbc.Button("Tipp absenden", id="guess-button", n_clicks=0, color="primary", className="mt-2"),
                    html.Div(id="guess-result", style={"marginTop": "1em", "fontWeight": "bold", "color": "#333"}),
                ], className="mb-3"),
                dcc.Graph(id="blind-map", style={"height": "600px"}),
                html.Div(id="score-display", className="mt-3 text-center"),
                html.Div(id="lists-display", className="mt-3 text-center"),
                dbc.Button("Zurück zur Kontinent-Auswahl", id="btn-back-to-screen-2", n_clicks=0, color="secondary", className="mt-3")
            ])
        ],
        id="screen-3",
        style={"display": "none", "maxWidth": "900px", "margin": "0 auto 2rem auto"}
    )
], fluid=True, className="pt-4")

###############################################################################
# 6) SCREEN VISIBILITY CALLBACK
###############################################################################
@app.callback(
    Output("screen-1", "style"),
    Output("screen-2", "style"),
    Output("screen-3", "style"),
    Input("store-current-screen", "data")
)
def switch_screens(current_screen):
    style_hidden = {"display": "none"}
    style_1 = {"display": "block", "maxWidth": "600px", "margin": "0 auto 2rem auto", "textAlign": "center"}
    style_2 = {"display": "block", "maxWidth": "600px", "margin": "0 auto 2rem auto"}
    style_3 = {"display": "block", "maxWidth": "900px", "margin": "0 auto 2rem auto"}
    if current_screen == 1:
        return style_1, style_hidden, style_hidden
    elif current_screen == 2:
        return style_hidden, style_2, style_hidden
    else:
        return style_hidden, style_hidden, style_3

###############################################################################
# 7) SCREEN NAVIGATION CALLBACK
###############################################################################
@app.callback(
    Output("store-current-screen", "data"),
    Input("btn-to-screen-2", "n_clicks"),
    Input("btn-to-screen-3", "n_clicks"),
    Input("btn-back-to-screen-2", "n_clicks"),
    State("store-current-screen", "data"),
    prevent_initial_call=True
)
def navigate_screens(n1, n2, n3, current_screen):
    ctx = callback_context
    if not ctx.triggered:
        return current_screen
    trig_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trig_id == "btn-to-screen-2":
        return 2
    elif trig_id == "btn-to-screen-3":
        return 3
    elif trig_id == "btn-back-to-screen-2":
        return 2
    return current_screen

###############################################################################
# 8) SAVE CHOSEN CONTINENT CALLBACK
###############################################################################
@app.callback(
    Output("store-chosen-continent", "data"),
    Input("continent-dropdown", "value"),
    State("store-chosen-continent", "data")
)
def set_continent(cont_val, old_val):
    if cont_val is None:
        return old_val
    return cont_val

###############################################################################
# 9) SINGLE CALLBACK FOR QUIZ LOGIC (Initialization & Guess Processing)
###############################################################################
@app.callback(
    Output("country-guess-dropdown", "options"),
    Output("store-selected-country", "data"),
    Output("guess-result", "children"),
    Output("store-correct-count", "data"),
    Output("store-wrong-count", "data"),
    Output("store-done-countries", "data"),
    Output("store-remaining-countries", "data"),
    Output("score-display", "children"),
    Output("lists-display", "children"),
    Output("country-guess-dropdown", "value"),  # Clear dropdown selection after guess
    Input("btn-to-screen-3", "n_clicks"),       # "Spiel starten"
    Input("guess-button", "n_clicks"),          # "Tipp absenden"
    State("store-chosen-continent", "data"),
    State("store-selected-country", "data"),
    State("store-correct-count", "data"),
    State("store-wrong-count", "data"),
    State("store-done-countries", "data"),
    State("store-remaining-countries", "data"),
    State("country-guess-dropdown", "value"),
    prevent_initial_call=True
)
def quiz_logic(start_click, guess_click,
               chosen_continent,
               current_country_de,
               correct_count,
               wrong_count,
               done_countries,
               remaining_countries,
               user_guess_de):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, "", correct_count, wrong_count, done_countries, remaining_countries, no_update, no_update, no_update

    trig_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Filter the DataFrame by chosen continent
    if not chosen_continent or chosen_continent == "Alle":
        sub_df = df
    else:
        sub_df = df[df["continent"] == chosen_continent]
        if sub_df.empty:
            sub_df = df

    message = ""

    # Initialize quiz when "Spiel starten" is clicked
    if trig_id == "btn-to-screen-3":
        correct_count = 0
        wrong_count = 0
        done_countries = []
        remaining_countries = sub_df["country_de"].tolist()
        if remaining_countries:
            current_country_de = random.choice(remaining_countries)
        else:
            current_country_de = None
        message = "Quiz initialisiert!"

    # Process guess when "Tipp absenden" is clicked
    elif trig_id == "guess-button":
        if not current_country_de:
            message = "Keine Länder mehr übrig oder Quiz nicht gestartet."
        else:
            if not user_guess_de:
                message = "Bitte wähle ein Land aus dem Dropdown!"
            else:
                if user_guess_de == current_country_de:
                    message = "Richtig! Neues Land wurde geladen."
                    correct_count += 1
                else:
                    message = f"Falsch! Richtig war: {current_country_de}"
                    wrong_count += 1
                if current_country_de not in done_countries:
                    done_countries.append(current_country_de)
                remaining_countries = [c for c in remaining_countries if c != current_country_de]
                if remaining_countries:
                    current_country_de = random.choice(remaining_countries)
                else:
                    message += " Quiz beendet!"
                    current_country_de = None

    # Build dropdown options from remaining countries only (thus already-done countries are removed)
    dropdown_options = [{"label": c, "value": c} for c in remaining_countries]

    # Build score and lists display
    score_display = dbc.Card(
        dbc.CardBody([
            html.H5("Aktueller Punktestand", className="card-title"),
            html.P(f"Korrekt: {correct_count}", className="card-text", style={"margin": "0"}),
            html.P(f"Falsch: {wrong_count}", className="card-text", style={"margin": "0"})
        ]),
        className="border p-2 d-inline-block"
    )
    lists_display = dbc.Card(
        dbc.CardBody([
            html.H6("Verbleibende Länder:"),
            html.P(", ".join(remaining_countries) if remaining_countries else "Keine mehr"),
            html.H6("Bereits gemacht:"),
            html.P(", ".join(done_countries) if done_countries else "Noch keine")
        ]),
        className="border p-2 mt-2"
    )

    return (dropdown_options,
            current_country_de,
            message,
            correct_count,
            wrong_count,
            done_countries,
            remaining_countries,
            score_display,
            lists_display,
            None)  # Clear dropdown selection

###############################################################################
# 10) UPDATE MAP CALLBACK
###############################################################################
@app.callback(
    Output("blind-map", "figure"),
    Input("store-selected-country", "data"),
    State("store-chosen-continent", "data")
)
def update_map(chosen_country_de, chosen_continent):
    if not chosen_country_de:
        return px.scatter(x=[0], y=[0], title="Bitte wähle einen Kontinent und starte das Spiel.")

    cont = chosen_continent if chosen_continent else "Alle"
    scope_val = scope_map.get(cont, "world")

    row = df.loc[df["country_de"] == chosen_country_de]
    selected_en = row["country_en"].values[0] if not row.empty else None

    df_map = df.copy()
    df_map["color"] = df_map["country_en"].apply(
        lambda x: "selected" if x == selected_en else "non-selected"
    )

    if cont == "Alle":
        sub_df_map = df_map
    else:
        sub_df_map = df_map[df_map["continent"] == cont]
        if sub_df_map.empty:
            sub_df_map = df_map

    fig = px.choropleth(
        sub_df_map,
        locations="country_en",
        locationmode="country names",
        color="color",
        color_discrete_map={"selected": "red", "non-selected": "lightgrey"},
        scope=scope_val,
        height=600
    )
    fig.update_layout(title=f"Karte ({cont})", showlegend=False)

    # Add micro-country markers (without labels)
    micro_data = {"country": [], "lat": [], "lon": [], "color": [], "size": []}
    for micro, coords in micro_coords.items():
        if micro in df["country_de"].values:
            if cont == "Alle" or micro in df[df["continent"] == cont]["country_de"].values:
                micro_data["country"].append(micro)
                micro_data["lat"].append(coords["lat"])
                micro_data["lon"].append(coords["lon"])
                if chosen_country_de == micro:
                    micro_data["color"].append("red")
                    micro_data["size"].append(12)
                else:
                    micro_data["color"].append("black")
                    micro_data["size"].append(8)
    if micro_data["country"]:
        fig.add_trace(go.Scattergeo(
            lon=micro_data["lon"],
            lat=micro_data["lat"],
            mode="markers",  # no text labels
            marker=dict(size=micro_data["size"], color=micro_data["color"]),
            showlegend=False
        ))
    return fig

###############################################################################
# 11) RUN THE FLASK SERVER
###############################################################################
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080)
