import streamlit as st

st.set_page_config(
    page_title="NiChart Viewer",
    page_icon="👋",
)

st.write("# Welcome to NiChart Viewer! 👋")

st.sidebar.success("Select a task")

st.markdown(
    """
    NiChart is an open-source framework built specifically for
    deriving Machine Learning based indices from MRI data.
    **👈 Select a task from the sidebar** to view your derived 
    data!
    ### Want to learn more?
    - Check out [NiChart Web page](https://neuroimagingchart.com)
    - Visit [NiChart GitHub](https://github.com/CBICA/NiChart_Project)
    - Jump into our [documentation](https://github.com/CBICA/NiChart_Project)
    - Ask a question in our [community
        forums](https://github.com/CBICA/NiChart_Project)
"""
)
