import streamlit as st
import pandas as pd
import pydeck as pdk
from urllib.error import URLError

st.set_page_config(page_title="Mapping Demo", page_icon="🌍")

filename = "../example_output/out_combined/Study1_DLMUSE_All"
output_data = pd.read_csv("../example_output/out_combined/Study1_DLMUSE_All")

st.markdown(f"# Active dataset: {filename}")

st.checkbox
