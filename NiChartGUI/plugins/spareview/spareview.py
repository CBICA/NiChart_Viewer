from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QLineEdit, QComboBox, QMenu, QAction, QWidgetAction
import sys, os
import pandas as pd
import gzip
import pickle
import numpy as np
from NiChartGUI.core.dataio import DataIO
# import dtale
from NiChartGUI.core.baseplugin import BasePlugin
from NiChartGUI.core import iStagingLogger
from NiChartGUI.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChartGUI.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChartGUI.core.gui.NestedQMenu import NestedQMenu
from NiChartGUI.core.model.datamodel import PandasModel

import inspect

import sys
#sys.path.append('/cbica/home/erusg/3_DEV/SPARE-Scores/05_niCHART/packaging/spare_scores')
#import spare_scores as spare

from spare_scores import spare_scores as spare

logger = iStagingLogger.get_logger(__name__)

class SpareView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(SpareView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None
        
        self.modelname = None
        self.modelname = '/home/guraylab/AIBIL/Github/NiChartPackages/NiChartHarmonize/test_temp/Test3/outputs/EXP2_ALL_TrainTest/spare_model.pkl.gz'

        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None


        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'spareview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        
        self.ui.wCalcSpare.hide()
        
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        
        self.ui.selectModelBtn.clicked.connect(self.OnSelectModelBtnClicked)
        self.ui.calcSpareBtn.clicked.connect(self.OnCalcSpareBtnClicked)


    def OnSelectModelBtnClicked(self):

        #if self.dataPathLast == '':
            #directory = QtCore.QDir().homePath()
        #else:
            #directory = self.dataPathLast
        directory = QtCore.QDir().homePath()
        directory = '/home/guraylab/AIBIL/Github/TmpPackages/SpareScores/mdl'
        directory = '/home/guraylab/AIBIL/Github/NiChartPackages/NiChartHarmonize/test_temp/Test3/outputs/EXP2_ALL_TrainTest'

        filename = QtWidgets.QFileDialog.getOpenFileName(None,
            caption = 'Open model file',
            directory = directory,
            filter = "Pickle/pickle.gz files (*.pkl *.gz)")

        if filename[0] == "":
            logger.warning("No file was selected")
        else:
            self.modelname = filename[0]
            self.ui.wCalcSpare.show()

    def OnCalcSpareBtnClicked(self):

        ## Read data and spare options
        df = self.data_model_arr.datasets[self.active_index].data
        outVarName = self.ui.edit_outVarName.text()
        if outVarName == '':
            outVarName = 'SPARE'
        if outVarName[0] == '_':
            outVarName = outVarName[1:]
        outCat = outVarName
        
        ## Apply SPARE
        dfOut = spare.spare_test(df, self.modelname)

        self.data_model_arr.datasets[self.active_index].data = df
        
        ## Create dict with info about new columns
        outDesc = 'Created by NiChartGUI SPARE Plugin'
        outSource = 'NiChartGUI SPARE Plugin'
            
        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        

        #dfOut = dfOut.round(3)
        self.PopulateTable(dfOut)
                                                                                                                        
        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        sub.setWindowTitle('SPARE Scores')
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        

    def PopulateTable(self, data):
        
        logger.info(data)
        logger.info('AAAAAAAAAAAAa')
        
        
        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    def OnDataChanged(self):
        
        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]

            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ### Update selection, sorting and drop duplicates panels
            #self.UpdatePanels(catNames, colNames)

