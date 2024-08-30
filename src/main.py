import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datasets import Datasets
from ICV_Normalization import ICV_Normalization
from Plot_Regression import Plot_Regression

class NiChartViewer(ctk.CTk):
    
    fname = 'EMPTY'
    
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.geometry("1500x1000")
        self.title("NiChart Viewer")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(expand=True, fill="both")

        self.datasets = self.tabview.add("Datasets")
        self.ICV_Norm = self.tabview.add("ICV Normalization")
        self.plot_reg = self.tabview.add("Plot Regression")

        self.datasets = Datasets(self.datasets, self.update_global)
        self.ICV_Norm = ICV_Normalization(self.ICV_Norm)
        self.plot_reg = Plot_Regression(self.plot_reg)
        
    def update_global(self, fname):
        self.fname = fname
        self.plot_reg.fname = fname
        print('HELLO !!!!!!!!!!!!!!!!!!!!!!!' + self.fname   )

if __name__ == "__main__":
    app = NiChartViewer()
    app.mainloop()
