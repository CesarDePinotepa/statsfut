# -*- coding: utf-8 -*-
"""

"""

# import relevant libraries (visualization, dashboard, data manipulation)
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from datetime import datetime
from statsbombpy import sb
from mplsoccer import VerticalPitch,Pitch
from highlight_text import ax_text, fig_text
from matplotlib.colors import LinearSegmentedColormap


@st.cache_data
def load_data():
    # Tabla de las competiciones abiertas de StatsBomb
    free_comps = sb.competitions()
    return free_comps


def shorten_name(name: str) -> str:
    """
    Shortens a name to include only the first name and last name.

    Parameters:
        name : The full name of a player.
    Return:
        The shortened name with only the first name and last name.
    """
    name_parts = name.split()
    return name_parts[0] + ' ' + name_parts[-1]


def get_opponent(match_string: str, local_team: str) -> str:
    """
    Extract the opponent team's name from the match string.

    Parameters:
        match_string : The match string containing both team names separated by ' vs '.
        local_team : The name of the local team.

    Returns:
        The name of the opponent team.
    """
    teams = match_string.split(' vs ')
    return teams[0] if teams[1] == local_team else teams[1]


def pass_map(player: str, vs_team: str, competition: str, completos: pd.DataFrame, incompletos: pd.DataFrame) -> plt:
    """

    :param player:
    :param vs_team:
    :param competition:
    :param completos:
    :param incompletos:
    :return:
    """
    # colores de las líneas en el gráfico
    white = "white"
    sbred = '#e21017'
    lightgrey = "#d9d9d9"
    darkgrey = '#9A9A9A'
    cmaplist = [white, darkgrey, sbred]
    cmap = LinearSegmentedColormap.from_list("", cmaplist)

    # Filtrando los pases solo del jugador seleccionado
    comp = completos[(completos["player"] == player)]
    incomp = incompletos[(incompletos["player"] == player)]

    # dibujando el campo de futbol
    pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black', line_zorder=2)

    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('white')

    # Contando los pases por zona y coordenadas x & y de finalizacion de los pases para el mapa de calor
    bin_statistic = pitch.bin_statistic(comp.pass_end_x, comp.pass_end_y, statistic='count', bins=(12, 8),
                                        normalize=True)
    pitch.heatmap(bin_statistic, ax=ax, alpha=0.5, cmap=cmap)

    # Graficando las flechas de los pases
    pitch.arrows(comp.x, comp.y, comp.pass_end_x, comp.pass_end_y, width=3,
                 headwidth=7, headlength=4, color=sbred, ax=ax, zorder=2, label="Completed pass")
    pitch.arrows(incomp.x, incomp.y, incomp.pass_end_x, incomp.pass_end_y, width=3,
                 headwidth=7, headlength=4, color=darkgrey, ax=ax, zorder=2, label="Incomplete pass")

    # etiquetas de color
    ax.legend(facecolor='white', handlelength=5, edgecolor='None', fontsize=20, loc='best')

    # titulo
    ax_title = ax.set_title(f'Pases de {player} vs {vs_team} - {competition}', fontsize=30, color='black')

    # plt.show()
    return fig


df_competitions = load_data()

###############################################################################
# Start building Streamlit App
###############################################################################
# side bar
df_unique_competitions = df_competitions['competition_name'].unique()
st.sidebar.title("Select Competition and Season")
selected_competition = st.sidebar.selectbox("Choose a competition", df_unique_competitions)
seasons = df_competitions[df_competitions['competition_name'] == selected_competition]['season_name'].unique()
selected_season = st.sidebar.selectbox("Choose a season", seasons)

df_selected_data = df_competitions[
    (df_competitions['competition_name'] == selected_competition) & (df_competitions['season_name'] == selected_season)]


season_id = df_selected_data['season_id'].iloc[0]
competition_id = df_selected_data['competition_id'].iloc[0]

# main column
# st.write(f"Season ID: {season_id}")
# st.write(f"Competition Name: {selected_competition}")
# st.write(f"Competition ID: {competition_id}")
# st.write(f"Season Name: {selected_season}")

# Partidos de la competicion seleccionada usando los ID's de competicion y temporada
df_current_competition = sb.matches(competition_id=competition_id, season_id=season_id)

# seleccionamos el equipo que nos interesa
unique_team = df_current_competition['home_team'].unique()
st.title("Select Team")
selected_team = st.selectbox("Choose a team", unique_team)
st.write(f"Team: {selected_team}")

# Filtramos a solo los partidos que nos interesan
df_selected_match = df_current_competition.loc[
    (df_current_competition['home_team'] == selected_team) | (df_current_competition['away_team'] == selected_team)]

# seleccionamos un encuentro
df_selected_match['match'] = df_selected_match['home_team'] + ' vs ' + df_selected_match['away_team']
st.title("Select a Match")
selected_match = st.selectbox("Choose a match", df_selected_match['match'].unique())
selected_match_id = df_selected_match[df_selected_match['match'] == selected_match]['match_id'].iloc[0]

st.write(f"Match: {selected_match}")
st.write(f"Match ID: {selected_match_id}")

# eventos de un partido en específico utilizando el ID del partido deseado
df_current_selected_match = sb.events(match_id=selected_match_id)
# st.dataframe(df_current_selected_match)

# filtrando solo las acciones de tipo "pass" en el partido específico
df_current_selected_match['type'].unique()
df_pases = df_current_selected_match[df_current_selected_match['type'] == 'Pass']
# separando las columnas donde se encuentran las coordenadas x,y juntas a columnas por separado
# primero creamos columnas nuevas 'x' & 'y' y las llenamos separando las coordenadas de la columna 'location'
# segundo, creamos las columnas x & y de las coordenadas donde termina el pase y llenamos separado 'pass_end_location'
# Separar las coordenadas 'x' e 'y' en columnas separadas
xy = df_pases['location'].apply(pd.Series)
xy.columns = ['x', 'y']
# Combinar las columnas 'x' e 'y' con el DataFrame original 'pases'
df_pases = pd.concat([df_pases, xy], axis=1)

pass_end_xy = df_pases['pass_end_location'].apply(pd.Series)
pass_end_xy.columns = ['pass_end_x', 'pass_end_y']
# Combinar las columnas 'pass_end_x' e 'pass_end_y' con el DataFrame original 'pases'
df_pases = pd.concat([df_pases, pass_end_xy], axis=1)

# seleccionando los pases del equipo seleccionado
df_pases_selected = df_pases[(df_pases["team"] == selected_team)]

# Aplicar la función shorten_name a la columna 'player'
# df_pases_selected['player'] = df_pases_selected['player'].apply(shorten_name)

# contamos los pases totales por jugador del equipo seleccionado
df_pases_totales = df_pases_selected.groupby(['player'])['player'].count().to_frame()
# separamos los pases incompletos de los completos
# observamos las diferentes posibilidades de pase utilizando pases['pass_outcome'].unique()
df_pases_completos = df_pases_selected[df_pases_selected['pass_outcome'].isnull()]
df_pases_incompletos = df_pases_selected[df_pases_selected['pass_outcome'].notnull()]

# agrenado la cuenta de los pases completos e uncompletes a nuestra tabla de cuenta de pases
df_pases_totales['completos'] = df_pases_completos.groupby(['player'])['player'].count().to_frame()
df_pases_totales['incompletos'] = df_pases_incompletos.groupby(['player'])['player'].count().to_frame()
df_pases_totales = df_pases_totales.fillna(0)

# renombrando columnas y creando una columna de porcentaje de pases completos y creando un minimo de pases
df_pases_totales = df_pases_totales.rename(columns={'player': 'pases totales'})
df_pases_totales = df_pases_totales.reset_index()
df_pases_totales['Porcentaje %'] = df_pases_totales['completos'] / df_pases_totales['pases totales'] * 100
df_pases_totales = df_pases_totales.sort_values('Porcentaje %', ascending=False)

# Puedes crear una tabla de top 10 jugadores por separado y usar esto en el codigo de la gráfica
# df_top_10_porcentaje = df_pases_totales.sort_values('Porcentaje %', ascending=False)

st.dataframe(df_pases_totales)

# data viz
# Graficas de barras
# Puedes cambiar a grafica vertical utilizando ax.bar en lugar de as.barh (intentalo!)
away_team = get_opponent(selected_match, selected_team)

st.title(f"Mejor porcentaje de pases vs {away_team}")
chart = st.bar_chart(df_pases_totales.set_index('player'))
st.write("Eje X: Porcentaje de pases")
st.write("Eje Y: Jugador")

# graficando en el campo de futbol
st.title("Player pass detail")
selected_player = st.selectbox("Choose a player", df_pases_totales['player'].unique())

fig = pass_map(player=selected_player, vs_team=away_team, competition=selected_competition,
               completos=df_pases_completos, incompletos=df_pases_incompletos)

st.pyplot(fig)
