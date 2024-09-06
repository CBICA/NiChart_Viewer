import streamlit as st
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.figure_factory as ff
import plotly.express as px
import os

st.set_page_config(page_title="Plotting Demo", page_icon="📈")

st.markdown("# Data visualization")
st.sidebar.header("Data visualization")
st.write(
    """
        This page will output the result plots that the user requested
    """
)


def sidebar() -> None:
    """
        Sidebar stuff
    """
    st.sidebar.image("../resources/nichart1.png")
    with st.sidebar:
        st.markdown("# Data visualization page")
        st.markdown("In order to run the whole pipeline, please click on `Run options` on the left panel \
        and provide your input and output folder, the total studies and the total cores you want \
        the pipelines to use. Once the pipelines run, you will have all the results in the output folder \
        you provided. Then, you can visualize all the results via the main charts on this page. \
        ")
    with st.sidebar.expander("Run options"):
        input_folder = st.text_input("path to input folder")
        output_folder = st.text_input("path to output folder")
        studies = st.text_input("total studies")
        cores = st.text_input("total cores")
        
        if not os.path.exists(input_folder):
            st.warning("Path to input folder don't exist")
        if not os.path.exists(output_folder):
            st.warning("Path to output folder don't exist")

        if st.button("Run w_sMRI"):
            st.write("Pipeline is running, please wait!")
            os.system("cd ../../NiCHart_Project/src/workflow")
            os.system(f"cd ../../NiChart_Project && python3 run.py --dir_input {input_folder} --dir_output {output_folder} --studies {studies} --cores {cores} --conda 1")
            st.write("Run completed!")

        if st.button("Run Segmentation"):
            st.write("Segmentation is not yet supported. This feature will be added soon!")

    st.sidebar.info("""
                    Currently, we only support the w_sMRI pipeline. Please visit the github repo for further updates regarding new features.

                    Note: This website is based on materials from the [NiChart Project](https://neuroimagingchart.com/).
                    The content and the logo of NiChart are intellectual property of [CBICA](https://www.med.upenn.edu/cbica/).
                    Make sure that you read the [licence](https://github.com/CBICA/NiChart_Project/blob/main/LICENSE).
                    """)

    with st.sidebar.expander("Acknowledgments"):
        st.markdown("""
                    The CBICA Dev team
                    """)


# Read output data 
output_data_list = []
output_data_hash = {}

for root, dirs, files in os.walk("../user_output"):
    for file in files:
        if file.endswith('.csv'):
            filepath = os.path.join(root, file)

            if os.path.getsize(filepath) == 0:
                continue

            df = pd.read_csv(filepath)
            output_data_list.append(file)
            output_data_hash[file] = df

output_data_selection = st.selectbox("Select output csv", output_data_list, index=4) # index is 4 because we only need dlmuse all for now 
output_data = output_data_hash[output_data_selection]

def distribution_plot() -> None:
    """
    Distribution plot
    """
    st.write(
            """
                Distribution plot
            """
    )
    valid_columns = [col_name for col_name, col_type in output_data.dtypes.items() 
                 if pd.api.types.is_integer_dtype(col_type) or pd.api.types.is_float_dtype(col_type)]
    dist_selection = st.selectbox("Select element for distribution plot", valid_columns)

    x1 = output_data[f'{dist_selection}']
    hist_data = [x1]
    group_labels = [f'{dist_selection} Volume'] 

    dist_plot = ff.create_distplot(
            hist_data, group_labels, bin_size = [.0]
    )

    dist_plot.update_layout(title={'text':f'Distribution plot of {dist_selection}', 'x': 0.4})
    st.plotly_chart(dist_plot, use_container_width=True)



def typical_plot() -> None:
    """
    Typical Y to Age plot
    """
    ICV_Column = st.selectbox(
            "ICV Column",
            output_data.columns,
    )

    st.line_chart(output_data, x="Age", y=f"{ICV_Column}")



def scatter_plot() -> None:
    """
        Scatter plot
    """

    if 'count_scatter_plots' not in st.session_state:
        st.session_state.count_scatter_plots = 0

    st.write("""
                Scatter plot
            """)

    def add_scatter_plot(index: int) -> None:
        #TODO: I dont know what this does, it's on the original viewer so i added it as an option
        #      so this needs to change the plot
        reference_sample = st.selectbox(
                "Reference Sample",
                ("Healthy control", "Healthy control, female", "Healthy control male", "..."),
                key=f"reference_sample_{index}"
                )
        Y_var_selector = st.selectbox(
                "Y Var",
                output_data.columns,
                key=f"Y_var_selector_{index}"
                )
        Hue_var_selector = st.selectbox(
                "Hue Var",
                output_data.columns,
                key=f"Hue_var_selector_{index}"
                )

        scatter_plot = px.scatter(output_data, x=f'{Y_var_selector}', y=f'{Hue_var_selector}')
        scatter_plot.update_layout(title={'text':f'Scatter plot of {Y_var_selector} and {Hue_var_selector}', 'x': 0.4})
        st.plotly_chart(scatter_plot)

    if st.button("Add plot"):
        st.session_state.count_scatter_plots += 1

    if st.button("Reset plots"):
        st.session_state.count_scatter_plots = 0

    for i in range(st.session_state.count_scatter_plots):
        st.write(f"Scatter plot {i + 1}")
        add_scatter_plot(i)


if __name__ == "__main__":
    sidebar()
    distribution_plot()
    typical_plot()
    scatter_plot()
