import streamlit as st
from streamlit_option_menu import option_menu

def pages_menu1():
    # Show a navigation menu for all pages
    st.sidebar.page_link("NiChartProject.py", label="Home")
    st.sidebar.write('---')

def pages_menu():
    with st.sidebar:
        selected = option_menu("Menu", ["Home", 'Settings'],
            icons=['house', 'gear'], default_index=0)

    if selected == "Home":
        st.write("home is where the heart is")
    else:
        st.switch_page("pages/1_PlotData.py")



