import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# seaborn example
from string import ascii_letters
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from tkinter import Button

# seaborn in matplotlib - tkinter doesn't need it
#import matplotlib
#matplotlib.use('TkAgg')

# embed matplotlib in tkinter 
import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Plot_Regression(ctk.CTk):

    def __init__(self, parent):
        ctk.set_appearance_mode("dark")
        self.parent = parent
        
        self.fname = 'EMPTY'
        
        # this is how you create the main window
        self.frame = ctk.CTkFrame(
            master=parent,
            height=950,
            width=1000,
            fg_color="black"
        )
        self.frame.place(relx=0.01, rely=0.02)

        self.row_counter = 1

        def button_event():
            sns.set(style="white")

            if self.fname == 'EMPTY':
                print('ERROR, no input csv!')
            else:

                # Read input csv
                d = pd.read_csv(self.fname)

                # Set up the matplotlib figure
                fig, ax = plt.subplots(figsize=(11, 9))

                # Create reg plot
                sns.regplot(data=d, x='Age', y='DLICV')

                ## Add it to canvas
                canvas = FigureCanvasTkAgg(fig, master=self.frame)
                #canvas.get_tk_widget().grid(row=1,column=4,columnspan=3,rowspan=20)
                canvas.get_tk_widget().grid(row=self.row_counter, column=0)
                canvas.draw()
                #canvas.get_tk_widget().pack()
                self.row_counter += 1 
                
                print('click ' + str(self.row_counter))
        
        
        self.button = ctk.CTkButton(parent, text="Plot", command=button_event)
        self.button.place(relx=0.815, rely=0.145)


#if __name__ == "__main__":
    #CTK_Window = ctkApp()
