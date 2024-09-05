import streamlit as st
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.figure_factory as ff
import plotly.express as px

st.set_page_config(page_title="Plotting Demo", page_icon="📈")

st.markdown("# Data visualization")
st.sidebar.header("Data visualization")
st.write(
    """
        This page will output the result plots that the user requested
    """
)

# Read output data 
output_data = pd.read_csv("../example_output/out_combined/Study1_DLMUSE_All.csv")

############ DISTRIBUTION PLOT ##########
st.write(
        """
            Distribution plot
        """
)

x1 = output_data['GM']
hist_data = [x1]
group_labels = ['GM Volume'] 

dist_plot = ff.create_distplot(
        hist_data, group_labels, bin_size = [.0]
)

dist_plot.update_layout(title={'text':'Distribution plot of GM', 'x': 0.3})
st.plotly_chart(dist_plot, use_container_width=True)

############ END OF DISTRIBUTION PLOT ##########


############ TYPICAL Y TO AGE PLOT ############

ICV_Column = st.selectbox(
        "ICV Column",
        output_data.columns,
)

st.line_chart(output_data, x="Age", y=f"{ICV_Column}")

############ END OF TYPICAL Y TO AGE PLOT ############


############ SCATTER PLOT #############

st.write("""
            Scatter plot
         """)

#TODO: I dont know what this does, it's on the original viewer so i added it as an option
#      so this needs to change the plot 
reference_sample = st.selectbox(
        "Reference Sample",
        ("Healthy control", "Healthy control, female", "Healthy control male", "..."),
        )
Y_var_selector = st.selectbox(
        "Y Var",
        output_data.columns
        )
Hue_var_selector = st.selectbox(
        "Hue Var",
        output_data.columns
        )

scatter_plot = px.scatter(output_data, x=f'{Y_var_selector}', y=f'{Hue_var_selector}')
scatter_plot.update_layout(title={'text':f'Scatter plot of {Y_var_selector} and Age', 'x': 0.3})
scatter_plot

############ END OF SCATTER PLOT ##########


############ START OF SPECIALIZED PLOTS ############



############ END OF SPECIALIZED PLOTS #############

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
