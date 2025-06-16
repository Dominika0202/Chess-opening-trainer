import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Chess Opening Trainer", layout="wide")
st.title("Chess Opening Trainer")

# some project introduction
st.markdown("""
Welcome to the **Chess Opening Trainer**!  
This website is designed to help you explore, analyze, and train your chess openings using pre-cleaned real game data.

Use the tabs in the sidebar to:
- Analyze player and game statistics
- Train specific openings by move
- Study positions and FENs where White or Black is to move
""")

# # LOAD THE DATASET
@st.cache_data
def load_data(file_path, sep=";", n_rows=None, index_col=None):
    print(f"Cache miss: Loading data from {file_path}...")
    df = pd.read_csv(file_path, sep=sep, nrows=n_rows, index_col=index_col)
    return df

# Define the file path
base_path = Path(__file__).resolve().parent

# Load into session_state if not already loaded
if "df" not in st.session_state:
    file_path = "pages/data/games_clean.csv"
    st.session_state.df = load_data(file_path, index_col="ID")

if "white_to_move_fens" not in st.session_state:
    file_path = "pages/data/white_to_move_fens.csv"
    st.session_state.white_to_move_fens = load_data(file_path, index_col="ID")

if "black_to_move_fens" not in st.session_state:
    file_path = "pages/data/black_to_move_fens.csv"
    st.session_state.black_to_move_fens = load_data(file_path, index_col="ID")

df = st.session_state.df

# select statistics
st.subheader("Dataset Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Games", f"{len(df):,}")

with col2:
    st.metric("Unique Openings", df['Opening'].nunique())

with col3:
    st.metric("Average Game Length", f"{df['Moves'].apply(lambda x: len(str(x).split())).mean():.1f} moves")

# dataset preview
with st.expander("Show sample data", expanded=False):
    st.dataframe(df.head(10))
