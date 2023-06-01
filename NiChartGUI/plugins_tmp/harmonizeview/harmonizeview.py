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

from NiChartHarmonize import nh_apply_model as nh_test

logger = iStagingLogger.get_logger(__name__)

class HarmonizeView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(HarmonizeView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None
        
        self.modelname = None
        ##self.modelname = '/home/guraylab/AIBIL/Github/TmpPackages/HarmonizeScores/mdl/mdl_SPARE_AD_MUSE_single.pkl.gz'

        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None


        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'harmonizeview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        
        self.ui.wCalcHarmonize.hide()
        
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        
        self.ui.selectModelBtn.clicked.connect(self.OnSelectModelBtnClicked)
        self.ui.calcHarmonizeBtn.clicked.connect(self.OnCalcHarmonizeBtnClicked)


    def CheckModel(self, filename):
        #read input data
        
        # Load model
        with gzip.open(filename, 'rb') as f:
            self.mdl = pickle.load(f)
            
        # Get columns and check if they exist in dset
        mdlCol = self.mdl['predictors']
        dfCol = self.data_model_arr.datasets[self.active_index].data.columns

        dfMdl = pd.DataFrame(columns=['Predictor'], data = mdlCol)
        dfMdl['Status'] = dfMdl.Predictor.isin(dfCol)
        dfMdl = dfMdl.replace({True:'FOUND', False:'MISSING'}).sort_values('Status', ascending = False)
        
        self.PopulateTable(dfMdl)

        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        sub.setWindowTitle('MODEL: ' + os.path.basename(filename))
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        
        if dfMdl[dfMdl.Status=='MISSING'].shape[0] > 0:
            self.statusbar.showMessage('WARNING: Model does not match the data!')
        
        else:
            self.ui.wCalcHarmonize.show()
            self.statusbar.showMessage('Model is valid')
            
        
        logger.critical(dfMdl.head())

    def OnSelectModelBtnClicked(self):

        #if self.dataPathLast == '':
            #directory = QtCore.QDir().homePath()
        #else:
            #directory = self.dataPathLast
        directory = QtCore.QDir().homePath()
        directory = '/home/guraylab/AIBIL/Github/TmpPackages/HarmonizeScores/mdl'

        filename = QtWidgets.QFileDialog.getOpenFileName(None,
            caption = 'Open model file',
            directory = directory,
            filter = "Pickle/pickle.gz files (*.pkl *.gz)")

        if filename[0] == "":
            logger.warning("No file was selected")
        else:
            self.modelname = filename[0]
            self.ui.wCalcHarmonize.show()


    def OnCalcHarmonizeBtnClicked(self):

        ## Read data and harmonize options
        df = self.data_model_arr.datasets[self.active_index].data
        outVarName = self.ui.edit_outVarName.text()
        if outVarName == '':
            outVarName = 'HARM'
        if outVarName[0] == '_':
            outVarName = outVarName[1:]
        outCat = outVarName
        
        ## Apply Harmonization
        res_harm = nh_test.nh_harmonize_to_ref(df, self.modelname)
        
        if len(res_harm) == 1:          ## Model mismatch
            logger.warning('AAAAAAAAAAAAAAAAAAA')

        else:
            mdlOut, dfOut = res_harm
        
        ## Set updated dset
        df = dfOut
        self.data_model_arr.datasets[self.active_index].data = df
        
        ## Create dict with info about new columns
        outDesc = 'Created by NiChartHarmonize Plugin'
        outSource = 'NiChartHarmonize Plugin'
        ##self.data_model_arr.AddNewVarsToDict([outVarName], outCat, outDesc, outSource)
            
        ## Call signal for change in data
        ##self.data_model_arr.OnDataChanged()
        
        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        
        ## Show only columns involved in application
        
        #dfOut = dfOut.round(3)
        self.PopulateTable(dfOut)
                                                                                                                        
        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        sub.setWindowTitle('Harmonized Values')
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        

    def PopulateTable(self, data):
        
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

