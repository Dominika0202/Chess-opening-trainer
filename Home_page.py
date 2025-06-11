import streamlit as st
import pandas as pd
from pathlib import Path

st.title("♟️ Chess Insights Hub")


# # LOAD THE DATASET
@st.cache_data 
def load_data(file_path, sep=";", n_rows=None, index_col = None):
    print(f"Cache miss: Loading data from {file_path}...")
    df = pd.read_csv(file_path, sep=sep, nrows=n_rows, index_col = index_col)
    return df

# Define the file path
base_path = Path(__file__).resolve().parent

# Load into session_state if not already loaded
if "df" not in st.session_state:
    file_path = "pages/data/games_clean.csv"
    st.session_state.df = load_data(file_path, index_col = "ID")


if "white_to_move_fens" not in st.session_state:
    file_path = "pages/data/white_to_move_fens.csv"
    st.session_state.white_to_move_fens = load_data(file_path, index_col = "ID")

if "black_to_move_fens" not in st.session_state:
    file_path = "pages/data/black_to_move_fens.csv"
    st.session_state.black_to_move_fens = load_data(file_path, index_col = "ID")
