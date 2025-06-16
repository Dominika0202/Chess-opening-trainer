import streamlit as st
import pandas as pd
import altair as alt

# we set page title
st.title("Statistics")
st.markdown("""
Welcome to the Statistics page, here you can view through the respective tabs certain statistics regarding the chosen dataseet of chess games.

To ensure smooth performance and avoid browser memory issues, this page operates on a **random sample of up to 50,000 games** from the full dataset.  
If the dataset contains fewer than 50,000 games, the entire dataset is used.
""")

# function to load data
df = st.session_state.df

# Take a consistent sample to reduce memory usage
sampled_df = df.sample(n=50000, random_state=42) if len(df) > 50000 else df.copy()

# check if movelist exists, if not make sure moves is a string then convert to list via split
if "MoveList" not in sampled_df.columns:
    sampled_df["MoveList"] = sampled_df["Moves"].apply(lambda m: str(m).split())

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

# ELO Distribution
with tab_elo:
    st.header("ELO Distribution")
    st.markdown("""
    This chart displays the overall distribution of player Elo ratings in the dataset.  
    Both White and Black Elo values are combined into a single histogram, allowing us to look at overall player rating.  
    The bars represent how frequently different Elo ranges occur among all players.
    """)
    elo_df = pd.concat([sampled_df['WhiteElo'], sampled_df['BlackElo']]).dropna()
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

# Opening Popularity
with tab_openings:
    st.header("Openings Popularity")
    st.markdown("""
    This chart shows the 25 most commonly played chess openings in the dataset.  
    It is based on the frequency of the `Opening` label recorded for each game.  
    This can be used to identify which openings are most common in the dataset.
    """)
    opening_counts = sampled_df["Opening"].value_counts().reset_index()
    opening_counts.columns = ["Opening", "Count"]
    top_openings = opening_counts.head(25)
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

# Game Results
with tab_results:
    st.header("Game Results")
    st.markdown("""
    This pie chart breaks down the distribution of game outcomes:  
    - `1-0` indicates a White win  
    - `0-1` indicates a Black win  
    - `1/2-1/2` indicates a draw  
    Each slice represents the proportion of games with that result, helping visualize outcomes.
    """)
    result_counts = sampled_df["Result"].value_counts().reset_index()
    result_counts.columns = ["Result", "Count"]
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

# Game Duration
with tab_duration:
    st.header("Game Duration")
    st.markdown("""
    This histogram shows the distribution of game lengths, measured in number of moves.  
    Each bar represents how many games fell into a certain move-count range.  
    The `MoveList` column is used to compute the number of moves per game.
    """)
    sampled_df["MoveCount"] = sampled_df["MoveList"].apply(len)
    chart_duration = (
        alt.Chart(sampled_df)
        .mark_bar()
        .encode(
            alt.X("MoveCount", bin=alt.Bin(maxbins=100)),
            y="count()",
            tooltip=["count()"]
        )
        .properties(title="Distribution of Game Durations")
    )
    st.altair_chart(chart_duration, use_container_width=True)

# Win Rate by Opening
with tab_winrate:
    st.header("Win Rate by Opening")
    st.markdown("""
    This section analyzes the performance of each opening in terms of win rates.  
    We calculate the percentage of games won by White, by Black, and that ended in a draw, for each opening.
    You can:
    - Filter to include only openings with a minimum number of games (for reliability).
    - Sort the openings by win rate of either White or Black.
    - Adjust how many top openings to display in the bar chart.
    These stats help identify which openings tend to be more successful for each side.
    """)
    opening_total = sampled_df["Opening"].value_counts().rename_axis("Opening").reset_index(name="TotalGames")
    white_wins = sampled_df[sampled_df["Result"] == "1-0"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="WhiteWins")
    black_wins = sampled_df[sampled_df["Result"] == "0-1"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="BlackWins")
    draws = sampled_df[sampled_df["Result"] == "1/2-1/2"]["Opening"].value_counts().rename_axis("Opening").reset_index(name="Draws")
    winrate_df = opening_total.merge(white_wins, on="Opening", how="left") \
                              .merge(black_wins, on="Opening", how="left") \
                              .merge(draws, on="Opening", how="left")
    winrate_df = winrate_df.fillna(0)
    winrate_df["WhiteWin%"] = (winrate_df["WhiteWins"] / winrate_df["TotalGames"]) * 100
    winrate_df["BlackWin%"] = (winrate_df["BlackWins"] / winrate_df["TotalGames"]) * 100
    winrate_df["Draw%"] = (winrate_df["Draws"] / winrate_df["TotalGames"]) * 100
    min_games = st.slider("Minimum number of games to include", min_value=1, max_value=1000, value=50)
    filtered_winrate = winrate_df[winrate_df["TotalGames"] >= min_games]
    sort_metric = st.selectbox("Sort by win percentage:", ["WhiteWin%", "BlackWin%"])
    filtered_winrate = filtered_winrate.sort_values(by=sort_metric, ascending=False)
    top_n = st.slider("Number of openings to display", min_value=5, max_value=50, value=25)
    display_df = filtered_winrate.head(top_n)[
        ["Opening", "TotalGames", "WhiteWin%", "BlackWin%", "Draw%"]
    ]
    st.dataframe(display_df.reset_index(drop=True))
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

# Termination Types
with tab_termination:
    st.header("Termination Types")
    st.markdown("""
    This chart shows the counts of termination reasons recorded in games.  
    Termination types include normal (e.g. checkmate, resignation, and various draw rules) and timeout.  
    The counts are displayed here.
    """)
    term_counts = sampled_df["Termination"].value_counts().reset_index()
    term_counts.columns = ["Termination", "Count"]
    top_termination = term_counts.head(10)
    chart_termination = (
        alt.Chart(top_termination)
        .mark_bar()
        .encode(
            y=alt.Y("Termination", sort="-x"),
            x="Count",
            tooltip=["Termination", "Count"]
        )
        .properties(title="Termination Reasons")
    )
    st.altair_chart(chart_termination, use_container_width=True)

# Time Controls
with tab_timecontrols:
    st.header("Time Controls")
    st.markdown("""
    This chart displays the most frequently used time controls in the dataset.  
    Time controls indicate the pace of the game, such as blitz, rapid, or classical formats.  
    Each bar shows how often a given time control occurred across all games.
    """)
    tc_counts = sampled_df["TimeControl"].value_counts().reset_index()
    tc_counts.columns = ["TimeControl", "Count"]
    top_timecontrols = tc_counts.head(10)
    chart_timecontrols = (
        alt.Chart(top_timecontrols)
        .mark_bar()
        .encode(
            y=alt.Y("TimeControl", sort="-x"),
            x="Count",
            tooltip=["TimeControl", "Count"]
        )
        .properties(title="Time Controls")
    )
    st.altair_chart(chart_timecontrols, use_container_width=True)
