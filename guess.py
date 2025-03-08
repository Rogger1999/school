###############################################################################
# main.py
###############################################################################
import random
import pandas as pd
import plotly.express as px

from flask import Flask
# Ab Dash 2.9 kannst du callback_context direkt importieren:
from dash import Dash, dcc, html, Input, Output, State, callback_context

from countries_data import countries_data  # <-- Hier liegen deine Länder-Daten

###############################################################################
# 1) DATAFRAME
###############################################################################
df = pd.DataFrame(countries_data)

###############################################################################
# 2) SCOPE-MAPPING
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
# 3) FLASK + DASH (nur Flask, kein Uvicorn)
###############################################################################
flask_app = Flask(__name__)
app = Dash(__name__, server=flask_app)  # Läuft standardmäßig unter http://127.0.0.1:8050/

###############################################################################
# 4) LAYOUT: 3 "SCREENS"
###############################################################################
app.layout = html.Div([
    dcc.Store(id="store-current-screen", data=1),         # 1=Willkommen, 2=Kontinent, 3=Quiz
    dcc.Store(id="store-chosen-continent", data=None),    # gewählter Kontinent
    dcc.Store(id="store-selected-country", data=None),     # aktuell gesuchtes Land (DE-Name)

    # --- SCREEN 1 (Willkommen) ---
    html.Div(
        id="screen-1",
        children=[
            html.H1("Mina & Valentina – Willkommen!", style={"textAlign": "center"}),
            html.P("Kleines Länder-Ratespiel auf einer Blindkarte.", style={"textAlign": "center"}),
            html.Button("Weiter", id="btn-to-screen-2", n_clicks=0,
                        style={"display": "block", "margin": "20px auto"})
        ],
        style={
            "border": "2px solid #ccc",
            "padding": "20px",
            "display": "block",
            "maxWidth": "600px",
            "margin": "20px auto",
            "textAlign": "center"
        }
    ),

    # --- SCREEN 2 (Kontinent) ---
    html.Div(
        id="screen-2",
        children=[
            html.H2("Kontinent auswählen"),
            dcc.Dropdown(
                id="continent-dropdown",
                options=[{"label": "Alle", "value": "Alle"}] + [
                    {"label": c, "value": c} for c in sorted(df["continent"].unique())
                ],
                placeholder="Kontinent wählen...",
                style={"width": "300px", "marginBottom": "20px"}
            ),
            html.Button("Spiel starten", id="btn-to-screen-3", n_clicks=0),
        ],
        style={
            "border": "2px solid #ccc",
            "padding": "20px",
            "display": "none",
            "maxWidth": "600px",
            "margin": "20px auto"
        }
    ),

    # --- SCREEN 3 (Quiz) ---
    html.Div(
        id="screen-3",
        children=[
            html.H2("Länder-Ratespiel (Blindkarte)"),
            html.Div([
                html.Label("Welches Land ist rot markiert?"),
                dcc.Dropdown(id="country-guess-dropdown", style={"width": "300px"}),
                html.Button("Tipp absenden", id="guess-button", style={"marginLeft": "10px"}),
                html.Div(id="guess-result", style={"marginTop": "1em", "fontWeight": "bold"}),
            ], style={"marginBottom": "20px"}),

            dcc.Graph(id="blind-map"),

            html.Button("Zurück zur Kontinent-Auswahl", id="btn-back-to-screen-2", n_clicks=0,
                        style={"marginTop": "20px"})
        ],
        style={
            "border": "2px solid #ccc",
            "padding": "20px",
            "display": "none",
            "maxWidth": "800px",
            "margin": "20px auto"
        }
    ),
])

###############################################################################
# 5) SCREENS-EIN-/AUSBLENDEN
###############################################################################
@app.callback(
    Output("screen-1", "style"),
    Output("screen-2", "style"),
    Output("screen-3", "style"),
    Input("store-current-screen", "data")
)
def switch_screens(current_screen):
    style_hidden = {"display": "none"}
    style_s1 = {"display": "block", "border": "2px solid #ccc", "padding": "20px",
                "maxWidth": "600px", "margin": "20px auto", "textAlign": "center"}
    style_s2 = {"display": "block", "border": "2px solid #ccc", "padding": "20px",
                "maxWidth": "600px", "margin": "20px auto"}
    style_s3 = {"display": "block", "border": "2px solid #ccc", "padding": "20px",
                "maxWidth": "800px", "margin": "20px auto"}

    if current_screen == 1:
        return style_s1, style_hidden, style_hidden
    elif current_screen == 2:
        return style_hidden, style_s2, style_hidden
    else:
        return style_hidden, style_hidden, style_s3

###############################################################################
# 6) SCREEN-WECHSEL
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
    # Hier verwenden wir callback_context aus dash >= 2.9:
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
# 7) KONTINENT SPEICHERN
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
# 8) EINZIGER CALLBACK FÜR COUNTRY & RESULT & DROPDOWN
###############################################################################
@app.callback(
    Output("country-guess-dropdown", "options"),
    Output("store-selected-country", "data"),
    Output("guess-result", "children"),
    Input("store-current-screen", "data"),   # Falls wir auf Screen 3 wechseln
    Input("guess-button", "n_clicks"),       # Falls Tipp-Button geklickt
    State("store-chosen-continent", "data"),
    State("country-guess-dropdown", "value"),
    State("store-selected-country", "data"),
    prevent_initial_call=True
)
def manage_country_and_message(screen_val, guess_clicks,
                               chosen_continent,
                               user_guess_de,
                               current_country_de):
    ctx = callback_context
    if not ctx.triggered:
        return [], None, ""

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Falls wir NICHT Screen 3 sind -> alles leer
    if screen_val != 3:
        return [], None, ""

    # 1) Kontinent filtern
    if not chosen_continent or chosen_continent == "Alle":
        sub_df = df
    else:
        sub_df = df[df["continent"] == chosen_continent]
        if sub_df.empty:
            sub_df = df

    # 2) Dropdown-Optionen
    dropdown_opts = [
        {"label": row["country_de"], "value": row["country_de"]}
        for _, row in sub_df.iterrows()
    ]

    # 3) Falls wir noch kein Land haben => zufälliges wählen
    if not current_country_de:
        new_country_de = random.choice(sub_df["country_de"].tolist())
    else:
        new_country_de = current_country_de

    # 4) Standard-Message
    msg = ""

    # 5) Wenn guess-button geklickt -> Tipp prüfen
    if triggered_id == "guess-button":
        if not user_guess_de or not new_country_de:
            msg = "Bitte zuerst ein Land auswählen!"
        else:
            if user_guess_de == new_country_de:
                msg = "Richtig! Neues Land wurde geladen."
                new_country_de = random.choice(sub_df["country_de"].tolist())
            else:
                msg = f"Falsch! Richtig war: {new_country_de}"

    return dropdown_opts, new_country_de, msg

###############################################################################
# 9) KARTE
###############################################################################
@app.callback(
    Output("blind-map", "figure"),
    Input("store-selected-country", "data"),
    State("store-chosen-continent", "data")
)
def update_map(chosen_country_de, chosen_continent):
    if not chosen_country_de:
        fig_empty = px.scatter(
            x=[0],
            y=[0],
            title="Bitte wähle einen Kontinent und starte das Spiel."
        )
        return fig_empty

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
        color_discrete_map={
            "selected": "red",
            "non-selected": "lightgrey"
        },
        scope=scope_val
    )
    fig.update_layout(title=f"Karte ({cont})", showlegend=False)
    return fig

###############################################################################
# 10) START (Flask-Server)
###############################################################################
if __name__ == "__main__":
    # Startet auf http://127.0.0.1:8050/
    app.run_server(debug=True, port=8080)
