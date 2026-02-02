import streamlit as st
from app import run_app
if __name__ == "__main__":
    st.set_page_config(page_title="Lattice Genie", layout="wide")
    run_app()
