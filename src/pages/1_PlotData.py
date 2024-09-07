import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import plotly.express as px
from math import ceil

# Initiate Session State Values
if 'instantiated' not in st.session_state:
    st.session_state.plots = pd.DataFrame({'PID':[]})
    st.session_state.pid = 1
    st.session_state.instantiated = True

def add_plot():
    '''
    Adds a new plot (updates a dataframe with plot ids)
    '''
    df_p = st.session_state.plots
    df_p.loc[st.session_state.pid] = [f'Plot {st.session_state.pid}']
    st.session_state.pid += 1

# Remove a plot
def remove_plot(pid):
    '''
    Removes the plot with the pid (updates the plot ids dataframe)
    '''
    df_p = st.session_state.plots
    df_p = df_p[df_p.PID != pid]
    st.session_state.plots = df_p

def display_plot(pid):
    '''
    Displays the plot with the pid
    '''

    # Create a copy of dataframe for filtered data
    df_filt = df.copy()

    # Main container for the plot
    plot_container = st.container(border=True)
    with plot_container:

        # Tabs for parameters
        ptabs = st.tabs([":lock:", ":large_orange_circle:", ":large_yellow_circle:",
                         ":large_green_circle:", ":x:"])

        # Tab 0: to hide other tabs

        # Tab 1: to set plotting parameters
        with ptabs[1]:
            plot_type = st.selectbox("Plot Type", ["DistPlot", "RegPlot"], key=f"plot_type_{pid}")
            # x_var = st.selectbox("X Var", df_filt.columns, key=f"x_var_{pid}", index=3)
            # y_var = st.selectbox("Y Var", df_filt.columns, key=f"y_var_{pid}", index=8)

            # Set index for default values
            x_ind = df.columns.get_loc(st.session_state.x_var)
            y_ind = df.columns.get_loc(st.session_state.y_var)
            hue_ind = df.columns.get_loc(st.session_state.hue_var)

            x_var = st.selectbox("X Var", df_filt.columns, key=f"x_var_{pid}", index = x_ind)
            y_var = st.selectbox("Y Var", df_filt.columns, key=f"y_var_{pid}", index = y_ind)
            hue_var = st.selectbox("Hue Var", df_filt.columns, key=f"hue_var_{pid}", index = hue_ind)

        # Tab 2: to set data filtering parameters
        with ptabs[2]:
            df_filt = filter_dataframe(df, pid)

        # Tab 3: to set centiles
        with ptabs[3]:
            cent_type = st.selectbox("Centile Type", df_filt.columns, key=f"cent_type_{pid}")

        # Tab 4: to reset parameters or to delete plot
        with ptabs[4]:
            st.button('Delete Plot', key=f'p_delete_{pid}',
                      on_click=remove_plot, args=[pid])

        # Main plot
        scatter_plot = px.scatter(df_filt, x = 'Age', y = y_var, color = hue_var, trendline="ols")
        st.plotly_chart(scatter_plot)


def filter_dataframe(df: pd.DataFrame, pid) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """

    df_init = df.copy()
    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    # Create filters selected by the user
    modification_container = st.container()
    with modification_container:
        widget_no = pid + '_filter'
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns, key = widget_no)
        for vno, column in enumerate(to_filter_columns):
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                widget_no = pid + '_col_' + str(vno)
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                    key = widget_no,
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    # Print sample size after filtering
    dim1, dim2 = df.shape
    st.success("Sample size is: " + str(dim1))

    return df

# Config page
st.set_page_config(page_title="DataFrame Demo", page_icon="📊", layout='wide')

# FIXME: Input data is hardcoded here for now
fname = "../examples/test_input/vTest1/Study1/StudyTest1_DLMUSE_All.csv"
df = pd.read_csv(fname)

# Page controls in side bar
with st.sidebar:

    # Slider to set number of plots in a row
    st.session_state.plot_per_raw = st.slider('Plots per raw',1, 5, 3, key='a_per_page')
    st.write('---')

    # Default x and y axis
    DEFAULT_XVAR = 'Age'
    DEFAULT_YVAR = 'GM'
    DEFAULT_HUEVAR = 'Sex'

    def_ind_x = 0
    if DEFAULT_XVAR in df.columns:
        def_ind_x = df.columns.get_loc(DEFAULT_XVAR)

    def_ind_y = 0
    if DEFAULT_YVAR in df.columns:
        def_ind_y = df.columns.get_loc(DEFAULT_YVAR)

    def_ind_hue = 0
    if DEFAULT_HUEVAR in df.columns:
        def_ind_hue = df.columns.get_loc(DEFAULT_HUEVAR)

    st.session_state.x_var = st.selectbox("Default X Var", df.columns, key=f"x_var_init", index = def_ind_x)
    st.session_state.y_var = st.selectbox("Default Y Var", df.columns, key=f"y_var_init", index = def_ind_y)
    st.session_state.hue_var = st.selectbox("Default Hue Var", df.columns, key=f"hue_var_init", index = def_ind_hue)
    st.write('---')

    # Button to add a new plot
    if st.button("Add plot"):
        add_plot()

# Read plot ids
df_p = st.session_state.plots
p_index = df_p.PID.tolist()
plot_per_raw = st.session_state.plot_per_raw

# Render plots
#  - iterates over plots;
#  - for every "plot_per_raw" plots, creates a new columns block, resets column index, and displays the plot
for i in range(0, len(p_index)):
    column_no = i % plot_per_raw
    if column_no == 0:
        blocks = st.columns(plot_per_raw)
    with blocks[column_no]:
        display_plot(p_index[i])

# # FIXME: this is for debugging for now; will be removed
# # with st.expander('Saved DataFrames'):
# with st.container():
#     st.session_state.plots


