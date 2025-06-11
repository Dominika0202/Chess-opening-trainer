import streamlit as st
from pathlib import Path
import pandas as pd
import altair as alt

# we set page title
st.title("Statistics")

# function to load data
df = st.session_state.df

# check if movelist exists, if not make sure moves is a string then convert to list via split
if "MoveList" not in df.columns:
    df["MoveList"] = df["Moves"].apply(lambda m: str(m).split())

# we define the tabs in the page
stats_tabs = [
    "ELO Distribution",
    "Opening Popularity",
    "Results",
    "Game Duration",
    "Win Rate by Opening",
    "Termination Types",
    "Time Controls"
]
(
    tab_elo,
    tab_openings,
    tab_results,
    tab_duration,
    tab_winrate,
    tab_termination,
    tab_timecontrols
) = st.tabs(stats_tabs)

# we define elo distribution contents
with tab_elo:
    # setting tab header
    st.header("ELO Distribution")

    # new df containing elo regardless of side
    elo_df = pd.concat([df['WhiteElo'], df['BlackElo']]).dropna()

    # altair chart
    chart_elo = (
        alt.Chart(pd.DataFrame({"ELO": elo_df}))
        .mark_bar()
        .encode(
            alt.X("ELO", bin=alt.Bin(maxbins=100)),
            y="count()",
            tooltip=["count()"]
        )
        .properties(title="Distribution of Player ELO Ratings")
    )
    st.altair_chart(chart_elo, use_container_width=True)

# we define openings popularity contents
with tab_openings:
    # tab header
    st.header("Openings Popularity")

    # new df containing info about occurrence count of each opening
    opening_counts = df["Opening"].value_counts().reset_index()
    opening_counts.columns = ["Opening", "Count"]
    # new df containing top 25 most popular openings
    top_openings = opening_counts.head(25)

    # altair chart
    chart_openings = (
        alt.Chart(top_openings)
        .mark_bar()
        .encode(
            y=alt.Y("Opening", sort="-x"),
            x="Count",
            tooltip=["Opening", "Count"]
        )
        .properties(title="Top 25 Chess Openings Popularity")
    )
    st.altair_chart(chart_openings, use_container_width=True)

# we define game results contents
with tab_results:

    # setting tab header
    st.header("Game Results")

    # new df counting each result occurrence
    result_counts = df["Result"].value_counts().reset_index()
    result_counts.columns = ["Result", "Count"]

    # altair chart
    chart_results = (
        alt.Chart(result_counts)
        .mark_arc()
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Result", type="nominal"),
            tooltip=["Result", "Count"]
        )
        .properties(title="Distribution of Game Results")
    )
    st.altair_chart(chart_results, use_container_width=True)

# we define game duration contents
with tab_duration:

    # setting tab header
    st.header("Game Duration")

    # new column to count moves
    df["MoveCount"] = df["MoveList"].apply(len)

    # altair chart
    chart_duration = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("MoveCount", bin=alt.Bin(maxbins=100)),
            y="count()",
            tooltip=["count()"]
        )
        .properties(title="Distribution of Game Durations")
    )
    st.altair_chart(chart_duration, use_container_width=True)

# we define win rate by opening contents
with tab_winrate:

    # setting tab header
    st.header("Win Rate by Opening")

    # 4 new dfs detailing occurrence of each opening in total and depending on result
    opening_total = df["Opening"].value_counts().rename_axis("Opening").reset_index(name="TotalGames")
    white_wins = df[df["Result"] == "1-0"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="WhiteWins")
    black_wins = df[df["Result"] == "0-1"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="BlackWins")
    draws = df[df["Result"] == "1/2-1/2"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="Draws")

    # combining the 4 dfs
    winrate_df = opening_total.merge(white_wins, on="Opening", how="left") \
                              .merge(black_wins, on="Opening", how="left") \
                              .merge(draws, on="Opening", how="left")
    winrate_df = winrate_df.fillna(0)

    # % calculation
    winrate_df["WhiteWin%"] = (winrate_df["WhiteWins"] / winrate_df["TotalGames"]) * 100
    winrate_df["BlackWin%"] = (winrate_df["BlackWins"] / winrate_df["TotalGames"]) * 100
    winrate_df["Draw%"] = (winrate_df["Draws"] / winrate_df["TotalGames"]) * 100

    # asking user input to filter out openings based on min occurrence
    min_games = st.slider("Minimum number of games to include", min_value=1, max_value=1000, value=50)
    filtered_winrate = winrate_df[winrate_df["TotalGames"] >= min_games]

    # asking user input to filter by side
    sort_metric = st.selectbox(
        "Sort by win percentage:",
        ["WhiteWin%", "BlackWin%"]
    )

    # sort winrate in descending order
    filtered_winrate = filtered_winrate.sort_values(by=sort_metric, ascending=False)

    # show top 25 openings based on previously defined user input
    top_n = st.slider("Number of openings to display", min_value=5, max_value=50, value=25)
    display_df = filtered_winrate.head(top_n)[
        ["Opening", "TotalGames", "WhiteWin%", "BlackWin%", "Draw%"]
    ]

    st.dataframe(display_df.reset_index(drop=True))

    # altair chart
    chart_winrate = (
        alt.Chart(display_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{sort_metric}:Q", title=f"{sort_metric} (%)"),
            y=alt.Y("Opening:N", sort="-x", title=""),
            color=alt.Color(f"{sort_metric}:Q", scale=alt.Scale(scheme="blues")),
            tooltip=[
                "Opening",
                "TotalGames",
                alt.Tooltip("WhiteWin%", format=".2f"),
                alt.Tooltip("BlackWin%", format=".2f"),
                alt.Tooltip("Draw%", format=".2f"),
            ],
        )
        .properties(title=f"Top {top_n} Openings by {'White' if sort_metric=='WhiteWin%' else 'Black'} Win%")
    )
    st.altair_chart(chart_winrate, use_container_width=True)

# we define termination types content
with tab_termination:

    # setting tab header
    st.header("Termination Types")

    # new df to count terminations
    term_counts = df["Termination"].value_counts().reset_index()
    term_counts.columns = ["Termination", "Count"]
    top_termination = term_counts.head(10)

    # altair chart
    chart_termination = (
        alt.Chart(top_termination)
        .mark_bar()
        .encode(
            y=alt.Y("Termination", sort="-x"),
            x="Count",
            tooltip=["Termination", "Count"]
        )
        .properties(title="Top 10 Termination Reasons")
    )
    st.altair_chart(chart_termination, use_container_width=True)

# we define time controls contents
with tab_timecontrols:

    # setting tab header
    st.header("Time Controls")

    # new df to count each occurrence of time control
    tc_counts = df["TimeControl"].value_counts().reset_index()
    tc_counts.columns = ["TimeControl", "Count"]
    top_timecontrols = tc_counts.head(10)

    # altair chart
    chart_timecontrols = (
        alt.Chart(top_timecontrols)
        .mark_bar()
        .encode(
            y=alt.Y("TimeControl", sort="-x"),
            x="Count",
            tooltip=["TimeControl", "Count"]
        )
        .properties(title="Top 10 Time Controls")
    )
    st.altair_chart(chart_timecontrols, use_container_width=True)
