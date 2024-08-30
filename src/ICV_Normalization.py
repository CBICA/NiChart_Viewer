import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ICV_Normalization(ctk.CTk):

    def __init__(self, parent):
        ctk.set_appearance_mode("dark")
        # this is how you create the main window
        self.frame = ctk.CTkFrame(
            master=parent,
            height=950,
            width=1000,
            fg_color="white"
        )
        self.frame.place(relx=0.01, rely=0.02)





if __name__ == "__main__":
    CTK_Window = ctkApp()
