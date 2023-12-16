# This Python file uses the following encoding: utf-8
"""
contact: software@cbica.upenn.edu
Copyright (c) 2018 University of Pennsylvania. All rights reserved.
Use of this source code is governed by license located in license file: https://github.com/CBICA/NiChartGUI/blob/main/LICENSE
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import argparse
import os, sys
from NiChartGUI.mainwindow import MainWindow
from NiChartGUI.NiChartGUICmdApp import NiChartGUICmdApp

def main():
    parser = argparse.ArgumentParser(description='NiChartGUI Data Visualization and Preparation')
    parser.add_argument('--data_file', type=str, help='Data file containing data frame.', default=None, required=False)
    parser.add_argument('--harmonization_model_file', type=str, help='Harmonization model file.', default=None, required=False)
    parser.add_argument('--SPARE_model_file', type=str, help='Model file for SPARE-scores.', default=None, required=False)
    parser.add_argument('--harmonize', type=str, help='Do harmonization or not.', default=None, required=False)
    parser.add_argument('--compute_spares', type=str, help='Compute SPARE-scores or not.', default=None, required=False)
    parser.add_argument('--output_file_name', type=str, help='Name of the output file with extension.', default=None, required=False)
    parser.add_argument("-nogui", action="store_true", help="Launch application in CLI mode to do data processing without any visualization or graphical user interface.")

    args = parser.parse_args(sys.argv[1:])

    data_file = args.data_file
    harmonization_model_file = args.harmonization_model_file
    SPARE_model_file = args.SPARE_model_file
    harmonize = args.harmonize
    compute_spares = args.compute_spares
    output_file = args.output_file_name
    noGUI = args.nogui


    if(noGUI):
        app = QtCore.QCoreApplication(sys.argv)
        if(compute_spares):
            if((data_file == None) or (SPARE_model_file == None) or (output_file == None)):
                print("Please provide '--data_file', '--SPARE_model_file' and '--output_file_name' to compute spares.")
                exit()
            NiChartGUICmdApp().ComputeSpares(data_file,SPARE_model_file,output_file)
    else:
        app = QtWidgets.QApplication(sys.argv)
        
        with open('./style.qss', 'r') as f:
            style = f.read()
            # Set the current style sheet
        app.setStyleSheet(style)

        
        mw = MainWindow(dataFile=data_file,
                        harmonizationModelFile=harmonization_model_file,
                        SPAREModelFile=SPARE_model_file)
        mw.show()

        #sys.exit(app.exec_())

if __name__ == '__main__':
    main()
