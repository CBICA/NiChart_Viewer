import streamlit as st

def pages_menu():
    # Show a navigation menu for all pages
    st.sidebar.page_link("NiChartProject.py", label="Home")
    st.sidebar.write('---')
    st.sidebar.page_link("pages/DLMUSE.py", label="sMRI Processing")
