import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import plotly.express as px

## Function definitions
def filter_dataframe(df: pd.DataFrame, cno) -> pd.DataFrame:
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
        widget_no = cno * 16
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns, key = widget_no)
        for vno, column in enumerate(to_filter_columns):
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                widget_no = cno * 16 + vno + 1
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
st.markdown("# Plot Data")
st.sidebar.header("Plot Data")
st.write(
    """View NiChart imaging variables and biomarkers
    """
)

# Set plot counter
if 'count_scatter_plots' not in st.session_state:
    st.session_state.count_scatter_plots = 0

if st.button("Add plot"):
    st.session_state.count_scatter_plots += 1

# Input data is hardcoded here
fname = "../examples/test_input/vTest1/Study1/StudyTest1_DLMUSE_All.csv"
df = pd.read_csv(fname)
#df = df.head(40)


# Create columns
cols = st.columns(st.session_state.count_scatter_plots + 1)

# Create plot in each column
for cno in range(0, st.session_state.count_scatter_plots+1):

    with cols[cno]:

        plot_container = st.container()
        with plot_container:

            st.write('Plot ' + str(cno + 1))

            cols2 = st.columns([1,1,1,1])

            with cols2[0]:
                # Filter data
                with st.popover(label='Filters'):
                    df_filt = filter_dataframe(df, cno)

            with cols2[1]:
                # Select vars
                with st.popover(label='Filters'):
                    df_filt2 = filter_dataframe(df, cno + 100)


            # # Display filtered dataframe
            # my_expander = st.expander(label='Data')
            # with my_expander:
            #     st.dataframe(df_filt)

            my_expander = st.expander(label='Plot', expanded = True)
            with my_expander:
                scatter_plot = px.scatter(df_filt, x = 'Age', y = 'GM')
                st.plotly_chart(scatter_plot)


