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
    # Answers-to-Questions is a one-to-many relationship
    st.session_state.plots = pd.DataFrame({'PID':[]})
    st.session_state.pid = 1
    st.session_state.instantiated = True

# Add a new plot block to the dataframe
def add_plot():
    df_p = st.session_state.plots
    # Create answer
    df_p.loc[st.session_state.pid] = [f'Plot {st.session_state.pid}']
    st.session_state.pid += 1
    st.text(st.session_state.pid)

# Remove a plot
def remove_plot(pid):
    df_p = st.session_state.plots
    st.session_state.plots = df_p.drop(pid)


# Display a plot
def display_plot(pid):

    # df_p = st.session_state.plots
    # plot_block = st.container()
    # a_block = qna_block.container()
    # q_block = qna_block.container()
    # mod_block = qna_block.container()

    ## Data frame with filtered data
    df_filt = df.copy()

    plot_container = st.container(border=True)
    with plot_container:

        st.write('Plot ' + pid)

        st.button('Remove Plot', key=f'p_remove_{pid}', on_click=remove_plot)


        my_expander = st.popover(label='Settings')
        with my_expander:
            tab1, tab2, tab3 = st.tabs(["Plot", "Filters", "Centiles"])
            with tab1:
                plot_type = st.selectbox("Plot Type", ["DistPlot", "RegPlot"], key=f"plot_type_{pid}")
                x_var = st.selectbox("X Var", df_filt.columns, key=f"x_var_{pid}")
                y_var = st.selectbox("Y Var", df_filt.columns, key=f"y_var_{pid}")

            with tab2:
                df_filt = filter_dataframe(df, pid)

            with tab3:
                cent_type = st.selectbox("Centile Type", df_filt.columns, key=f"cent_type_{pid}")

        # # Display filtered dataframe
        # my_expander = st.expander(label='Data')
        # with my_expander:
        #     st.dataframe(df_filt)

        my_expander = st.expander(label='Plot', expanded = True)
        with my_expander:

            scatter_plot = px.scatter(df_filt, x = 'Age', y = y_var)
            st.plotly_chart(scatter_plot)

        # st.button('Remove QnA', key=f'a_remove_{pid}', on_click=remove_plot, args=[pid])


## Function definitions
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
                # widget_no = cno * 16 + vno + 1
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

st.set_page_config(page_title="DataFrame Demo", page_icon="📊", layout='wide')
# st.set_page_config(page_title="DataFrame Demo", page_icon="📊")

# st.markdown("# Plot Data")
# st.sidebar.header("Plot Data")
# st.write(
#     """View NiChart imaging variables and biomarkers
#     """
# )

# Set plot counter
if 'count_scatter_plots' not in st.session_state:
    st.session_state.count_scatter_plots = 0

# Page controls in Sidebar
with st.sidebar:

    st.session_state.plot_per_raw = st.slider('Plots per raw',1, 10,5, key='a_per_page')
    st.write('---')
    # Button to add new answer block

    # st.button('New Plot')
    # # st.button('New Plot', on_click=add_answer)

    if st.button("Add plot"):
        add_plot()
        if st.session_state.count_scatter_plots < st.session_state.plot_per_raw - 1:
            st.session_state.count_scatter_plots += 1

# Input data is hardcoded here
fname = "../examples/test_input/vTest1/Study1/StudyTest1_DLMUSE_All.csv"
df = pd.read_csv(fname)
#df = df.head(40)


# Create columns
cols = st.columns(st.session_state.count_scatter_plots + 1)

# # Create plot in each column
# for cno in range(0, st.session_state.count_scatter_plots+1):
#     with cols[cno]:
#         display_plot(cno)


# Render plots
df_p = st.session_state.plots
p_index = df_p.PID.tolist()
plot_per_raw = st.session_state.plot_per_raw

for i in range(0, len(p_index)):
    cno = i % st.session_state.plot_per_raw
    if cno == 0:
        blocks = st.columns(plot_per_raw)
    with blocks[cno]:
        display_plot(p_index[i])
        # display_plot(plot_index[i])

with st.expander('Saved DataFrames'):
    st.session_state.plots


