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

        ### Read the df
        #input('fff')
        #self.button = ctk.CTkButton(master=parent, text='PLOT', command=self.create_plot(self.fname))
        #self.button.place(relx=0.715, rely=0.145)

        def button_event():
            sns.set(style="white")

            if self.fname == 'EMPTY':
                print('ERROR, no input csv!')
            else:

                d = pd.read_csv(self.fname)
                
                # Compute the correlation matrix
                #d = pd.DataFrame(data=[[1,2,3],[1,2,3],[1,2,3]], columns=['A','B','C'])
                #corr = d.corr()
                #print(corr.shape)

                # Set up the matplotlib figure
                fig, ax = plt.subplots(figsize=(11, 9))

                # Draw the heatmap with the mask and correct aspect ratio
                
                print(d.columns)
                #input()
                
                sns.regplot(data=d, x='Age', y='DLICV')

                ## Create the regression plot
                canvas = FigureCanvasTkAgg(fig, master=self.frame)
                canvas.draw()
                canvas.get_tk_widget().pack()
            
        self.button = ctk.CTkButton(parent, text="Plot", command=button_event)
        self.button.place(relx=0.815, rely=0.145)

    def create_plot(self, fname):
        print('HHHH ' + fname)

        sns.set(style="white")

        if fname != '':
            d = pd.read_csv(self.fname)
            d = pd.DataFrame(data=rs.normal(size=(100, 26)), columns=list(ascii_letters[26:]))
            
            # Compute the correlation matrix
            corr = d.corr()

            # Generate a mask for the upper triangle
            mask = np.zeros_like(corr, dtype=np.bool)
            mask[np.triu_indices_from(mask)] = True

            # Set up the matplotlib figure
            fig, ax = plt.subplots(figsize=(11, 9))

            # Generate a custom diverging colormap
            cmap = sns.diverging_palette(220, 10, as_cmap=True)

            # Draw the heatmap with the mask and correct aspect ratio
            sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0,
                        square=True, linewidths=.5, cbar_kws={"shrink": .5})

            ## Create the regression plot
            canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
            canvas.draw()
            canvas.get_tk_widget().pack()

#if __name__ == "__main__":
    #CTK_Window = ctkApp()
