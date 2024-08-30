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
        
        # this is how you create the main window
        self.frame = ctk.CTkFrame(
            master=parent,
            height=950,
            width=1000,
            fg_color="black"
        )
        self.frame.place(relx=0.01, rely=0.02)

        # This will create the regression plot
        self.select_data_textbox = ctk.CTkLabel(
            master=parent,

    def create_plot():
        sns.set(style="white")

        # Generate a large random dataset
        rs = np.random.RandomState(33)
        d = pd.DataFrame(data=rs.normal(size=(100, 26)),
                        columns=list(ascii_letters[26:]))

        # Compute the correlation matrix
        corr = d.corr()

        # Generate a mask for the upper triangle
        mask = np.zeros_like(corr, dtype=np.bool)
        mask[np.triu_indices_from(mask)] = True

        # Set up the matplotlib figure
        f, ax = plt.subplots(figsize=(11, 9))

        # Generate a custom diverging colormap
        cmap = sns.diverging_palette(220, 10, as_cmap=True)

        # Draw the heatmap with the mask and correct aspect ratio
        sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0,
                    square=True, linewidths=.5, cbar_kws={"shrink": .5})

        return f

if __name__ == "__main__":
    CTK_Window = ctkApp()



## --- main ---

#root = tkinter.Tk()
#root.wm_title("Embedding in Tk")

#label = tkinter.Label(root, text="Matplotlib with Seaborn in Tkinter")
#label.pack()

#fig = create_plot()

#canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
#canvas.draw()
#canvas.get_tk_widget().pack()

#button = tkinter.Button(root, text="Quit", command=root.destroy)
#button.pack()

#tkinter.mainloop()
