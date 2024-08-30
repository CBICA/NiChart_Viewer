import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import json
import pandas as pd
import pathlib
import tkinter as tk
from tkinter import ttk

# sets working directory to root dir
#os.chdir('../..')
os.chdir('..')

class Datasets(ctk.CTk):
    """
        Datasets class to preview the Datasets tab
        It supports the selection of a csv and previews it
        using treeview and tkinter
    """

    def __init__(self, parent, update_global):
        # set default mode to dark
        ctk.set_appearance_mode("dark")
        self.parent = parent
        
        # Function in main window to keep global vars
        self.update_global = update_global
        
        # This gets the info.json data that user requests
        #self.json_file = open("src/workflow/workflows/info.json")
        self.json_file = open("examples/info.json")        
        
        self.json_data = json.load(self.json_file)
        self.studies = self.json_data["studies"]

        # this is how you create the main window
        self.frame = ctk.CTkFrame(
            master=parent,
            height=900,
            width=1000,
            fg_color="white"
        )
        self.frame.place(relx=0.01, rely=0.02)

        # This will display the text to select the available data
        self.select_data_textbox = ctk.CTkLabel(
            master=parent,
            text="Select active dataset",
            corner_radius=10,  # Rounded corners
            fg_color="#2B2B2B",  # Soft dark background color
            text_color="white",  # White text color
            font=("Arial", 25),  # Larger, clean font
            width=300,  # Fixed width
            height=40,  # Fixed height
            padx=10,  # Padding inside the label
            pady=5,  # Padding inside the label
            anchor="w",  # Left-align the text
            justify="left"  # Justify the text to the left
        )
        self.select_data_textbox.place(relx=0.70, rely=0.100)

        # this is just a search for the csv files in all studies
        # in the end, the csv_options array will have all the csv files of all study folders
        self.csv_options = []
        self.csv_fullpath_options = {}
        for studies in self.studies:
            for csv_file in os.listdir(self.json_data["dir_input"] + f"/{str(studies)}"):
                self.csv_options.append(str(csv_file))
                self.csv_fullpath_options[str(csv_file)] = f"{os.getcwd()}" + "/" + self.json_data["dir_input"] + "/" + os.path.join(studies, csv_file)

        # Create a label to display the selected csv file
        self.selected_csv_file = ctk.CTkLabel(
                    master=parent,
                    text=f"Selected dataset: {self.csv_options[0]}",
                    corner_radius=10,  # Rounded corners
                    fg_color="#2B2B2B",  # Soft dark background color
                    text_color="white",  # White text color
                    font=("Arial", 25),  # Larger, clean font
                    width=300,  # Fixed width
                    height=40,  # Fixed height
                    padx=10,  # Padding inside the label
                    pady=5,  # Padding inside the label
                    anchor="w",  # Left-align the text
                    justify="left"  # Justify the text to the left
                )
        self.selected_csv_file.place(relx=0.70, rely=0.180)

        # Create a label to display the selected csv file's shape
        self.tmp_csv_select = pd.read_csv(self.csv_fullpath_options[self.csv_options[0]])
        self.selected_csv_shape = ctk.CTkLabel(
                    master=parent,
                    text=f"Data shape: {self.tmp_csv_select.shape}",
                    corner_radius=10,  # Rounded corners
                    fg_color="#2B2B2B",  # Soft dark background color
                    text_color="blue",  # White text color
                    font=("Arial", 25),  # Larger, clean font
                    width=300,  # Fixed width
                    height=40,  # Fixed height
                    padx=10,  # Padding inside the label
                    pady=5,  # Padding inside the label
                    anchor="w",  # Left-align the text
                    justify="left"  # Justify the text to the left
                )
        self.selected_csv_shape.place(relx=0.70, rely=0.220)

        # This function is used to update the Option menu, it will output which
        # dataset is selected
        def option_changed(selected_option):
            self.update_selected_csv(selected_option)

        # the next lines create a dropdown menu with values the action options(select columns or show data table)\
        self.selected_action = ctk.CTkLabel(
            master=parent,
            text=f"Select Action",
            corner_radius=10,  # Rounded corners
            fg_color="#2B2B2B",  # Soft dark background color
            text_color="white",  # White text color
            font=("Arial", 25),  # Larger, clean font
            width=300,  # Fixed width
            height=40,  # Fixed height
            padx=10,  # Padding inside the label
            pady=5,  # Padding inside the label
            anchor="w",  # Left-align the text
            justify="left"  # Justify the text to the left
        )
        self.selected_action.place(relx=0.70, rely=0.270)

        # add dropdown menu for action option
        self.dataframe_plotting_options = ["Show data table", "Select columns"]
        self.click_menu = ctk.StringVar(value=self.dataframe_plotting_options[0])
        self.dropdown_menu = ctk.CTkOptionMenu(master=parent, values=self.dataframe_plotting_options, command=option_changed)
        self.dropdown_menu.place(relx=0.715, rely=0.315)

        # the next lines create a dropdown menu with values the csv options
        self.click_menu = ctk.StringVar(value=self.csv_options[0])
        self.dropdown_menu = ctk.CTkOptionMenu(master=parent, values=self.csv_options, command=option_changed)
        self.dropdown_menu.place(relx=0.715, rely=0.145)

        # Create a Treeview to display the DataFrame
        self.tree = ttk.Treeview(master=self.frame)
        self.tree.place(relx=0.01, rely=0.01, relwidth=0.97, relheight=0.97)

        # Add a vertical scrollbar
        self.tree_scroll = ttk.Scrollbar(master=self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.place(relx=0.98, rely=0.01, relheight=0.97)
        self.show_data_table()

        # add a horizontal scrollbar
        self.tree_horizontal_scroll = ttk.Scrollbar(master=self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=self.tree_horizontal_scroll.set)
        self.tree_horizontal_scroll.place(relx=0.01, rely=0.98, relwidth=0.97)

    def update_selected_csv(self, selected_option):
       # Clear the textbox
       # Insert the new selected dataset
       self.selected_csv_file.configure(text=f"Selected dataset: {selected_option}")
       self.tmp_csv_select = pd.read_csv(self.csv_fullpath_options[selected_option])
       self.selected_csv_shape.configure(text=f"Data shape: {self.tmp_csv_select.shape}")
       self.show_data_table()
       self.update_global(self.csv_fullpath_options[selected_option])

    def show_data_table(self):
        # Clear the current treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Set up the columns
        self.tree["columns"] = list(self.tmp_csv_select.columns)
        self.tree["show"] = "headings"  # Show column headings

        # Create column headings
        for column in self.tree["columns"]:
            self.tree.heading(column, text=column)  # Let the column heading be the column name

        # Insert data into the treeview
        for index, row in self.tmp_csv_select.iterrows():
            self.tree.insert("", "end", values=list(row))
