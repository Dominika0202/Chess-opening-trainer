## LOAD THE PACKAGES
import streamlit as st
import chess
import chess.svg
import chess
import polars as pl
import pandas as pd
from typing import List
import altair as alt

# -----------------------------------------------------------------------------
# 0. PAGE CONFIGURATIONS
# -----------------------------------------------------------------------------
st.title("🧠 Chess Opening Trainer")

tab_titles = ["Easy version", "Hard Version"]
tab_easy, tab_hard = st.tabs(tab_titles)

# LOAD THE DATASET
@st.cache_resource # Note: for simple file loading, @st.cache_data is often preferred
def load_data_resource(file_path, sep = ";", n_rows = None):
    print(f"Cache miss: Loading data resource from {file_path}...")
    df = pd.read_csv(file_path, sep = sep, nrows = n_rows)
    return df

file = "games_clean.csv"
df = load_data_resource(file)

#### smaller test_df for now
test_df = df.head(100_000)

# -----------------------------------------------------------------------------
# 1. FUNCTIONS
# -----------------------------------------------------------------------------
# ------ 1.1 GENERAL FUNCTIONS ------
def get_board_svg(board, last_move=None, size=500):
    """
    Generates an SVG image of the chess board.
    """
    if last_move:
        #visualizes the last move
        return chess.svg.board(board=board, lastmove=last_move, size=size)
    return chess.svg.board(board=board, size=size)

def list_to_move_str(move_list):
    """
    Convert moves in a list into a string
    """
    moves_str = ""
    for i, move in enumerate(move_list):
        if i % 2 == 0: # White's move
            moves_str += f"{i//2 + 1}. {move} "
        else: # Black's move
            moves_str += f"{move} "
    return moves_str

def next_move_san(move_str: str, id = None):
    """
    Given a move id list return the move from a move string. If no id is given return none
    """
    if id == None:
        return None
    color, n = id
    move_n = (n-1)*3
    if color == "w":
        move_n += 1
    else:
        move_n += 2
    return move_str.split()[move_n]

def get_popular_next_moves(df):
    """
    Given a filtered data frame, returns a df of popular next moves with counts.
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


# ------ 1.2 EASY VERSION FUNCTIONS ------
def find_games_with_str_position(df: pd.DataFrame, my_moves: str):
    """
    Returns filtered data frame with the games that played the exact same moves as in move_str
    """
    mask = df["Moves"].str.contains(my_moves)
    return df.loc[mask].reset_index().copy()

def next_move_id(move_str):
    """
    Returns the id of the next move, e.g. ["w", 2] –> next move is white's second move
    """
    x = len(str.split(move_str))
    n = x//3 + 1
    if x%3 == 0:
        return ["w", n]
    else:
        return ["b", n]



def filter_data_move_str(df, move_str):
    """
    Given move string filter the data fram and attach a column with the next move
    """
    filtered = find_games_with_str_position(df, move_str).copy()
    id = next_move_id(move_str)
    filtered["Next_moves"] = filtered["Moves"].apply(lambda m: next_move_san(m, id))
    return filtered

# ------ 1.3 HARD VERSION (FEN) FUNCTIONS ------
def moves_to_fens(moves_str: str, max_moves: int = 20) -> List[str]:
    """
    Given a move string, returns a fen representation of each position that occured in the first "max_moves" moves.
    """
    board = chess.Board()
    fens = []
    tokens = moves_str.split()

    move_count = 0
    for token in tokens:
        if token.endswith('.'):
            continue  # skip move numbers ("1.", "2.")
        try:
            board.push_san(token) #d4 –> d2d4
            fens.append(board.epd())
            move_count += 1
            if move_count >= max_moves * 2:
                break
        except: #invalid move
            break 
    return fens


def next_move_id_fen(fen_moves: list[str], target_fen):
        try:
            id = fen_moves.index(target_fen) + 1
            n = id//2 + 1
            if id%2 == 0:
                return ["w", n]
            else:
                return ["b", n]
        except ValueError:
            return None

def find_games_fen(df: pd.DataFrame, board) -> pd.DataFrame:
    """
    Return all games in df whose move‐history reached the same
    board position as my_moves does.
    """

    if board == chess.Board():
        df["Next_moves"] = df["Moves"].apply(lambda m: next_move_san(m, ["w", 1]))
        return df
    
    target_fen = board.epd()


    # 3) filter
    position_list = df["FEN_Moves"].apply(lambda m: next_move_id_fen(m, target_fen))
    position_san = [next_move_san(m, l) for m,l in zip(df["Moves"], position_list)]
    df["Next_moves"] = position_san
    return df.dropna(subset = ["Next_moves"])

# -----------------------------------------------------------------------------
# 2. OPENING TRAINER EASY TAB
# -----------------------------------------------------------------------------

# ------ 2.1 CONFIGURATIONS ------
#These variables will not reload when a button is pressed
if 'board' not in st.session_state:
    st.session_state.board = chess.Board() # Initialize a new chess board
if 'move_history_san' not in st.session_state:
    st.session_state.move_history_san = [] # To store moves in Standard Algebraic Notation

#initialize the move string to recoment the moves before the start of the game
moves_str = ""

# ------ 2.1 PAGE LAYOUT ------
with tab_easy:
    st.header("Opening Trainer")
    st.write("Enter moves (e.g., `e4`, `Nf3`, `O-O`). The board will update, and you'll see insights.")

    col_board, col_info = st.columns([3, 2]) # Separates the page: Board takes 3/5 width, info 2/5

    with col_board:
        st.subheader("Current Position")

        # Display the current board SVG
        # Get the last move made to highlight it
        last_move = None
        if st.session_state.board.move_stack: #if a move has been played
            last_move = st.session_state.board.move_stack[-1]

        board_svg = get_board_svg(st.session_state.board, last_move=last_move, size=500)
        st.image(board_svg, use_column_width=True)

#------ 2.2 MOVE INPUT ------
        user_move_san = st.text_input("Enter your move:", key= "move_input", placeholder="e.g. e4, d4, Nf3")
        # Buttons: Make Move and Reset
        b1, b2, _ = st.columns([2,2,3])
        if b1.button("Make Move", key = "Make_Move",use_container_width=True):
            # This ensures we get the latest value if Enter was pressed (see Issue 2)
            if user_move_san:
                try:
                    # If a move is entered and the button is pressed, Attempt to parse and push the move
                    move = st.session_state.board.parse_san(user_move_san)
                    st.session_state.board.push(move) #push the move
                    st.session_state.move_history_san.append(user_move_san)
                    st.rerun() # Rerun to update board and info
                except ValueError as e:
                    # This includes illegal moves or ambiguous SAN
                    st.error(f"Invalid move: {user_move_san}. Reason: {e}")
            else:
                st.warning("Please enter a move to play.")

        if b2.button("Reset Board",key = "Reset", use_container_width=True):
            st.session_state.board = chess.Board() #reset the board
            st.session_state.move_history_san = []
            st.rerun()

#------ 2.2 INFO COLUMN ------
    with col_info:
        st.subheader("Position Insights")
        #------ 2.2.1 MOVE HISTORY ------
        st.write("**Move History:**")
        if st.session_state.move_history_san:
            moves_str = list_to_move_str(st.session_state.move_history_san)
            st.text_area("Played Moves", value=moves_str, height=150, disabled= True)
        else:
            st.info("No moves played yet.")
        st.write("---")

   
        #------ 2.2.1 POPULAR NEXT MOVES ------ UNIQUE TO EASY VERSION
        st.write("**Popular Next Moves:**")
        filtered_df = filter_data_move_str(test_df, moves_str)
        move_counts_df = get_popular_next_moves(filtered_df) # Pass board object

        # Build an Altair bar chart (horizontal)
        chart = (alt.Chart(move_counts_df).mark_bar().encode(
                x=alt.X("Count", title="Times Played"),
                y=alt.Y("Move", sort="-x", title = ""),
                tooltip=["Move", "Count"]) )

        st.altair_chart(chart, use_container_width=True)
        st.write("---")

        #------ 2.2.2 COMMON OPENINGS ------ UNIQUE TO EASY VERSION
        st.markdown("**Common Openings from this line:**")
        common_openings = get_common_openings(filtered_df)
        for i, opening in enumerate(common_openings):
                st.write(f"{i + 1}. {opening}")

        st.markdown("---")
    st.dataframe(filtered_df)


# -----------------------------------------------------------------------------
# 3. OPENING TRAINER FEN (HARD) TAB
# -----------------------------------------------------------------------------

#NOTE: All the code until 3.2.1 POPULAR NEXT MOVES is the same as before with _fen added to variable names and keys

# ------ 3.1 CONFIGURATIONS ------
#These variables will not reload when a button is pressed
if 'board_fen' not in st.session_state:
    st.session_state.board_fen = chess.Board() # Initialize a new chess board
if 'move_history_san_fen' not in st.session_state:
    st.session_state.move_history_san_fen = [] # To store moves in Standard Algebraic Notation


### Test df (for now)
test_fen = df.head(100)
#apply the moves_to_fens function
test_fen["FEN_Moves"] = test_fen["Moves"].apply(lambda m: moves_to_fens(m, max_moves=15))


# ------ 3.1 PAGE LAYOUT ------
with tab_hard:
    st.header("Opening Trainer")
    st.write("Enter moves (e.g., `e4`, `Nf3`, `O-O`). The board will update, and you'll see insights.")

    col_board_fen, col_info_fen = st.columns([3, 2]) # Separates the page: Board takes 3/5 width, info 2/5

    with col_board_fen:
        st.subheader("Current Position")

        # Display the current board SVG
        # Get the last move made to highlight it
        last_move_fen = None
        if st.session_state.board_fen.move_stack: #if a move has been played
            last_move_fen = st.session_state.board_fen.move_stack[-1]

        board_svg_fen = get_board_svg(st.session_state.board_fen, last_move=last_move_fen, size=500)
        st.image(board_svg_fen, use_column_width=True)

#------ 3.2 MOVE INPUT ------
        user_move_san_fen = st.text_input("Enter your move:", key= "move_input_fen", placeholder="e.g. e4, d4, Nf3")

        # Buttons: Make Move and Reset
        b1_fen, b2_fen, _ = st.columns([2,2,3])
        if b1_fen.button("Make Move", key = "Make_Move_fen", use_container_width=True):
            # This ensures we get the latest value if Enter was pressed (see Issue 2)
            if user_move_san_fen:
                try:
                    # If a move is entered and the button is pressed, Attempt to parse and push the move
                    move = st.session_state.board_fen.parse_san(user_move_san_fen)
                    st.session_state.board_fen.push(move) #push the move
                    st.session_state.move_history_san_fen.append(user_move_san_fen)
                    st.rerun() # Rerun to update board and info
                except ValueError as e:
                    # This includes illegal moves or ambiguous SAN
                    st.error(f"Invalid move: {user_move_san_fen}. Reason: {e}")
            else:
                st.warning("Please enter a move to play.")

        if b2_fen.button("Reset Board", key = "Reset_fen", use_container_width=True):
            st.session_state.board_fen = chess.Board() #reset the board
            st.session_state.move_history_san_fen = []
            st.rerun()

#------ 3.2 INFO COLUMN ------
    with col_info_fen:
        st.subheader("Position Insights")
        #------ 2.2.1 MOVE HISTORY ------
        st.write("**Move History:**")
        if st.session_state.move_history_san_fen:
            moves_str_fen = list_to_move_str(st.session_state.move_history_san_fen)
            st.text_area("Played Moves", value=moves_str_fen, height=150, disabled= True)
        else:
            st.info("No moves played yet.")
        st.write("---")

        # Get current FEN for analysis functions
        current_fen = st.session_state.board_fen.fen()
    
        #------ 3.2.1 POPULAR NEXT MOVES ------ UNIQUE TO EASY VERSION
        st.write("**Popular Next Moves:**")
        filtered_df_fen = find_games_fen(test_fen, st.session_state.board_fen)
        move_counts_df_fen = get_popular_next_moves(filtered_df_fen) # Pass board object
    
        # Build an Altair bar chart (horizontal)
        chart_fen = (alt.Chart(move_counts_df_fen).mark_bar().encode(
                x=alt.X("Count", title="Times Played"),
                y=alt.Y("Move", sort="-x", title = ""),
                tooltip=["Move", "Count"]) )

        st.altair_chart(chart_fen, use_container_width=True)
        st.write("---")

        #------ 3.2.2 COMMON OPENINGS ------ UNIQUE TO EASY VERSION
        st.markdown("**Common Openings from this line:**")
        common_openings_fen = get_common_openings(filtered_df_fen)
        for i, opening in enumerate(common_openings_fen):
                st.write(f"{i + 1}. {opening}")

        st.markdown("---")
    st.dataframe(filtered_df_fen)