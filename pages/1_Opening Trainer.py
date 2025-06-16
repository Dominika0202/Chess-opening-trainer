## LOAD THE PACKAGES
import streamlit as st
import chess.svg
import chess
import pandas as pd
import altair as alt
import numpy as np

# -----------------------------------------------------------------------------
# 0. PAGE CONFIGURATIONS
# -----------------------------------------------------------------------------
st.title("Chess Opening Trainer")

tab_titles = ["Simple Trainer", "Advanced Trainer"]
tab_easy, tab_hard = st.tabs(tab_titles)

df = st.session_state.df
white_to_move_fens = st.session_state.white_to_move_fens
black_to_move_fens = st.session_state.black_to_move_fens

# -----------------------------------------------------------------------------
# 1. FUNCTIONS
# -----------------------------------------------------------------------------
# ------ 1.1 GENERAL FUNCTIONS ------
def get_board_svg(board, last_move = None, size = 500, orientation = chess.WHITE):
    """
    Generates an SVG image of the chess board.
    """
    if last_move:
        #visualizes the last move
        return chess.svg.board(board = board, lastmove = last_move, size = size, orientation = orientation)
    return chess.svg.board(board = board, size = size, orientation = orientation)

def list_to_move_str(move_list):
    """
    Convert moves in a list into a string
    """
    moves_str = ""
    for i, move in enumerate(move_list):
        if i % 2 == 0: # White's move
            moves_str += f"{i // 2 + 1}. {move} "
        else: # Black's move
            moves_str += f"{move} "
    return moves_str.strip()

def next_move_san(move_str, id = None):
    """
    Given a move id list return the move from a move string. If no id is given return none.
    The id parameter expects [color, move_number].
    """
    if id == None:
        return None
    color, n = id
    move_n = (n-1) * 3
    if color == "w":
        move_n += 1
    else:
        move_n += 2
    try:
        return move_str.split()[move_n]
    except IndexError:
        return None

def next_move_id(move_str):
    """
    Returns the id of the next move. 
    Example move id: ["w", 2] -> next move is white's second move
    """
    x = len(str.split(move_str))
    n = x // 3 + 1
    if x % 3 == 0:
        return ["w", n]
    else:
        return ["b", n]

def get_popular_next_moves(df):
    """
    Given a filtered data frame, returns a df of 5 popular next moves with counts.
    """
    move_counts = df["Next_moves"].value_counts()
    counts_df = (move_counts.rename_axis("Move").reset_index(name="Count"))
    return counts_df.head(5)

def get_common_openings(df):
    """
    Given a filtered data frame, returns a list of the top 5 most common openings.
    """
    opening_counts = df["Opening"].value_counts()
    openings = opening_counts.index
    counts = opening_counts.values
    return openings[:5]

def top_games(df, board):
    """
    Returns information about top 5 games by white's/black's elo in the data frame
    """
    #get the color of the next move
    if board.turn == chess.WHITE:
        column = "WhiteElo"
    else:
        column = "BlackElo"

    top_games = df.sort_values(column, ascending = False).head(5)
    top_games["URL"] = [f"https://lichess.org/{i}" for i in top_games.index]
    top_games_info = top_games[["WhiteElo", "BlackElo", "Result", "URL"]]
    return top_games_info.reset_index(drop=True)


# ------ 1.2 SIMPLE IMPLEMENTATION FUNCTIONS ------
def find_games_with_str_position(df, move_str):
    """
    Returns filtered data frame with the games that played the exact same moves as in move_str
    """
    mask = df["Moves"].str.contains(move_str, regex = False) #perform literal substring search
    return df.loc[mask].reset_index().copy()


def filter_data_move_str(df, move_str):
    """
    Given move string filter the data frame and attach a column with the next move
    """
    filtered = find_games_with_str_position(df, move_str).copy()
    id = next_move_id(move_str)
    filtered["Next_moves"] = filtered["Moves"].apply(lambda m: next_move_san(m, id))
    return filtered

# ------ 1.3 ADVANCED IMPLEMENTATION (FEN) FUNCTIONS ------
def next_move_id_fen(fen_moves, target_fen):
        try:
            id = fen_moves.index(target_fen) + 1
            n = id//2 + 1
            if id % 2 == 0:
                return ["w", n]
            else:
                return ["b", n]
        except ValueError:
            return None

def find_games_fen(df, board):
    """
    Return all games in df whose move-history reached the same
    board position as on the board. Return also the next move information for each match.
    """
    #we check if the board is in the start position
    if board == chess.Board():
        df["Next_moves"] = df["Moves"].apply(lambda m: next_move_san(m, ["w", 1]))
        return df 
    
    target_fen = board.epd()

    #get the color of the next move
    if board.turn == chess.WHITE:
        to_move_c = "w"
        fens_df = white_to_move_fens #use white_to_move_fens for search
    else:
        to_move_c = "b"
        fens_df = black_to_move_fens #use black_to_move_fens for search
    
    #search for the target fen
    result = np.where(fens_df == target_fen)
    matched_game_ID = fens_df.index[result[0]].tolist()
    move_numbers = fens_df.columns[result[1]].astype(int)

    #filter the dataframe using the matched IDs
    df_filtered = df.loc[matched_game_ID]

    next_move_sans = [next_move_san(m, [to_move_c, n]) for m,n in zip(df_filtered["Moves"], move_numbers)]
    df_filtered["Next_moves"] = next_move_sans
    return df_filtered

# ------ 1.4 Default statistics (statistics of the starting position) ------
def stats_initialization():
    '''Calculate the baseline statistics from the start position'''
    moves_str = ""
    filtered = filter_data_move_str(df, moves_str) #we get the next moves
    popular_moves = get_popular_next_moves(filtered)
    common_opens = get_common_openings(filtered)
    return popular_moves, common_opens

if 'stats_initialization' not in st.session_state:
    st.session_state.stats_initialization = stats_initialization()

# -----------------------------------------------------------------------------
# 2. OPENING TRAINER EASY TAB
# -----------------------------------------------------------------------------

# ------ 2.1 CONFIGURATIONS ------
if 'board' not in st.session_state:
    st.session_state.board = chess.Board() # Initialize a new chess board
if 'move_history_san' not in st.session_state:
    st.session_state.move_history_san = [] # To store moves in Standard Algebraic Notation (SAN)
if 'orientation' not in st.session_state:
    st.session_state.orientation = chess.WHITE

#initialize the move string
moves_str = ""

# ------ 2.1 PAGE LAYOUT ------
with tab_easy:
    st.header("Direct Opening Trainer")
    st.write("This version provides statistics for the exact move-by-move line you've played. Note that if you reach the same position through a different move order, the results can be different.")
    st.write("Enter moves (e.g., `e4`, `Nf3`, `O-O`). The board will update, and you'll see insights.")

    col_board, col_info = st.columns([3, 2]) # Separates the page: Board takes 3/5 width, info 2/5

    with col_board:
        st.subheader("Current Position")
        
        #flip board button
        if st.button("Flip Board", key="flip"):
            # Check the current state and set it to the opposite
            if st.session_state.orientation == chess.WHITE:
                st.session_state.orientation = chess.BLACK
            else:
                st.session_state.orientation = chess.WHITE
        #show the svg board
        last_move = None
        if st.session_state.board.move_stack: #if a move has been played
            last_move = st.session_state.board.move_stack[-1]
        board_svg = get_board_svg(st.session_state.board, last_move = last_move, size = 500, orientation = st.session_state.orientation)
        st.image(board_svg, use_container_width=True)

#------ 2.2 MOVE INPUT ------
        def process_move():
            """
            Save the move and board if the move is legal.
            This function is called when the 'Make Move' button is clicked.
            """
            user_move = st.session_state.move_input
            if user_move:
                try:
                    move = st.session_state.board.parse_san(user_move)
                    user_move_san = st.session_state.board.san(move)
                    st.session_state.move_history_san.append(user_move_san)
                    st.session_state.board.push(move)

                    #Clear the input box for the next move.
                    st.session_state.move_input = ""

                except ValueError as e:
                    st.error(f"Invalid move: '{user_move}'.")
            else:
                st.warning("Please enter a move to play.")

        def reset_board():
            """
            Resets the board and the move history.
            This function is called when the 'Reset Board' button is clicked.
            """
            st.session_state.board = chess.Board()
            st.session_state.move_history_san = []
            st.session_state.move_input = ""

        with st.form(key="move_form"):
            st.text_input("Enter your move:", key = "move_input", placeholder = "e.g. e4, d4, Nf3")
            st.form_submit_button("Make Move", use_container_width = True, on_click=process_move)

        st.button("Reset Board", key = "Reset", use_container_width = True, on_click=reset_board)

#------ 2.3 POSITION INSIGHTS ------
    with col_info:
        st.subheader("Position Insights")

        #------ 2.3.1 MOVE HISTORY ------
        st.write("**Move History:**")
        if st.session_state.move_history_san:
            moves_str = list_to_move_str(st.session_state.move_history_san)
            st.text_area("Played Moves", value=moves_str, height=150, key = "Played_Moves", disabled= True)
        else:
            st.info("No moves played yet.")
        st.write("---")

        #------ 2.3.1 CALCULATIONS OF STATISTICS ------ UNIQUE TO THIS VERSION
        if moves_str:
            filtered_df = filter_data_move_str(df, moves_str)
            move_counts_df = get_popular_next_moves(filtered_df)
            common_openings = get_common_openings(filtered_df)
        else:
            filtered_df = df
            move_counts_df, common_openings = st.session_state.stats_initialization

        #------ 2.3.2 POPULAR NEXT MOVES ------
        st.write("**Popular Next Moves:**")
        # Build an Altair bar chart (horizontal)
        chart = (alt.Chart(move_counts_df).mark_bar().encode(
                x=alt.X("Count", title="Times Played"),
                y=alt.Y("Move", sort="-x", title = ""),
                tooltip=["Move", "Count"]) )

        st.altair_chart(chart, use_container_width=True)
        st.write("---")

        #------ 2.3.3 COMMON OPENINGS ------
        st.markdown("**Common Openings from this line:**")
        for i, opening in enumerate(common_openings):
                st.write(f"{i + 1}. {opening}")

        st.markdown("---")

        #------ 2.3.4 BEST GAMES DF ------
    with col_board:
        st.write("**Top Player Games from this Position**")
        st.write("Copy the link and see the full game")
        st.dataframe(top_games(filtered_df, st.session_state.board), key = "data_frame")
# -----------------------------------------------------------------------------
# 3. OPENING TRAINER FEN (HARD) TAB
# -----------------------------------------------------------------------------

#NOTE: All the code except 3.2.1 CALCULATIONS OF STATISTICS is the same as before with _fen added to variable names and keys.

# ------ 3.1 CONFIGURATIONS ------
if 'board_fen' not in st.session_state:
    st.session_state.board_fen = chess.Board() # Initialize a new chess board
if 'move_history_san_fen' not in st.session_state:
    st.session_state.move_history_san_fen = [] # To store moves in Standard Algebraic Notation
if 'orientation_fen' not in st.session_state:
    st.session_state.orientation_fen = chess.WHITE

#Initialize the move string
moves_str_fen = ""

# ------ 3.1 PAGE LAYOUT ------
with tab_hard:
    st.header("Advanced Opening Trainer")
    st.write("This version analyzes the board based on the current position, not the move order. It finds all games that reached this exact setup, even through a different sequence of moves. This gives you the most accurate insights into the position.")
    st.write("Because this version is more computationally intensive, it can be slightly slower. **Please note:** This advanced analysis is available for positions within the first 20 moves of a game.")
    st.write("Enter moves (e.g., `e4`, `Nf3`, `O-O`). The board will update, and you'll see insights.")

    col_board_fen, col_info_fen = st.columns([3, 2]) # Separates the page: Board takes 3/5 width, info 2/5

    with col_board_fen:
        st.subheader("Current Position")

        #flip board button
        if st.button("Flip Board", key="flip_fen"):
            # Check the current state and set it to the opposite
            if st.session_state.orientation_fen == chess.WHITE:
                st.session_state.orientation_fen = chess.BLACK
            else:
                st.session_state.orientation_fen = chess.WHITE

        # Display the current board SVG
        last_move_fen = None
        if st.session_state.board_fen.move_stack: #if a move has been played
            last_move_fen = st.session_state.board_fen.move_stack[-1]

        board_svg_fen = get_board_svg(st.session_state.board_fen, last_move = last_move_fen, size = 500, orientation = st.session_state.orientation_fen)
        st.image(board_svg_fen, use_container_width = True)

#------ 3.2 MOVE INPUT ------
        def process_move_fen():
            """This function is called when the 'Make Move' button is clicked."""
            user_move_fen = st.session_state.move_input_fen
            if user_move_fen:
                try:
                    move = st.session_state.board_fen.parse_san(user_move_fen)
                    user_move_san = st.session_state.board_fen.san(move)
                    st.session_state.move_history_san_fen.append(user_move_san)
                    st.session_state.board_fen.push(move)

                    #Clear the input box for the next move.
                    st.session_state.move_input_fen = ""

                except ValueError as e:
                    st.error(f"Invalid move: '{user_move_fen}'.")
            else:
                st.warning("Please enter a move to play.")

        def reset_board_fen():
            """This function is called when the 'Reset Board' button is clicked."""
            st.session_state.board_fen = chess.Board()
            st.session_state.move_history_san_fen = []
            st.session_state.move_input_fen = ""

        with st.form(key = "move_form_fen"):
            st.text_input("Enter your move:", key = "move_input_fen", placeholder = "e.g. e4, d4, Nf3")
            st.form_submit_button("Make Move", use_container_width = True, on_click = process_move_fen)

        st.button("Reset Board", key = "Reset_fen", use_container_width = True, on_click = reset_board_fen)

#------ 3.3 POSITION INSIGHTS ------
    with col_info_fen:
        st.subheader("Position Insights")

        #------ 3.3.1 MOVE HISTORY ------
        st.write("**Move History:**")
        if st.session_state.move_history_san_fen:
            moves_str_fen = list_to_move_str(st.session_state.move_history_san_fen)
            st.text_area("Played Moves", value=moves_str_fen, key = "Played_Moves_fen",height=150, disabled= True)
        else:
            st.info("No moves played yet.")
        st.write("---")    

        #------ 3.3.1 CALCULATIONS OF STATISTICS ------ UNIQUE TO THIS VERSION
        if moves_str_fen:
            filtered_df_fen = find_games_fen(df, st.session_state.board_fen)
            move_counts_df_fen = get_popular_next_moves(filtered_df_fen)
            common_openings_fen = get_common_openings(filtered_df_fen)
        else:
            filtered_df_fen = df
            move_counts_df_fen, common_openings_fen = st.session_state.stats_initialization


        #------ 3.3.2 POPULAR NEXT MOVES ------
        st.write("**Popular Next Moves:**")
        # Build an Altair bar chart (horizontal)
        chart_fen = (alt.Chart(move_counts_df_fen).mark_bar().encode(
                x=alt.X("Count", title="Times Played"),
                y=alt.Y("Move", sort="-x", title = ""),
                tooltip=["Move", "Count"]) )

        st.altair_chart(chart_fen, use_container_width=True)
        st.write("---")

        #------ 3.3.3 COMMON OPENINGS ------
        st.markdown("**Common Openings from this line:**")
        for i, opening in enumerate(common_openings_fen):
                st.write(f"{i + 1}. {opening}")

        st.markdown("---")
    
    with col_board_fen:
         #------ 3.3.4 BEST GAMES DF ------
        st.write("**Top Player Games from this Position**")
        st.write("Copy the link and see the full game")
        st.dataframe(top_games(filtered_df_fen, st.session_state.board_fen), key = "data_frame_fen")