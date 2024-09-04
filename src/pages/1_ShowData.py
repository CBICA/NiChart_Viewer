import streamlit as st
import pandas as pd
import altair as alt
from urllib.error import URLError

st.set_page_config(page_title="DataFrame Demo", page_icon="📊")

st.markdown("# Show Data")
st.sidebar.header("Show Data")
st.write(
    """View NiChart imaging variables and biomarkers
    """
)


@st.cache_data
def get_nichart_data():
    fname = "../examples/test_input/vTest1/Study1/StudyTest1_DLMUSE_All.csv"
    df = pd.read_csv(fname)
    return df


try:
    df = get_nichart_data()
    dx_ad = st.multiselect(
        "Choose DX_AD", list(df.DX_AD), ["CN", "MCI", "AD"]
    )
    if not dx_ad:
        st.error("Please select at least one DX for AD.")
    else:
        data = df[df.DX_AD.isin(dx_ad)]
        st.write("### NiChart data", df.head(10))

        #data = data.T.reset_index()
        #data = pd.melt(data, id_vars=["index"]).rename(
            #columns={"index": "year", "value": "Gross Agricultural Product ($B)"}
        #)
        #chart = (
            #alt.Chart(data)
            #.mark_area(opacity=0.3)
            #.encode(
                #x="year:T",
                #y=alt.Y("Gross Agricultural Product ($B):Q", stack=None),
                #color="Region:N",
            #)
        #)
        #st.altair_chart(chart, use_container_width=True)
except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason
    )
