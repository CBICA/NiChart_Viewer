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
from NiChartHarmonize import nh_learn_model as nh_train

logger = iStagingLogger.get_logger(__name__)

class HarmonizeView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(HarmonizeView, self).__init__()

        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None

        self.TH_NUM_UNIQ = 20

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'harmonizeview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for action
        self.ui.comboBoxAction = QComboBox(self.ui)
        self.ui.comboBoxAction.setEditable(False)
        self.ui.vlAction.addWidget(self.ui.comboBoxAction)
        self.PopulateComboBox(self.ui.comboBoxAction, ['LearnModel', 'ApplyModel'], '--action name--')
        
        ## Panel for primary key
        self.ui.comboBoxPrimaryKeyVar = QComboBox(self.ui)
        self.ui.comboBoxPrimaryKeyVar.setEditable(False)
        self.ui.vlPrimaryKeyVar.addWidget(self.ui.comboBoxPrimaryKeyVar)
        
        ## Panel for batch var
        self.ui.comboBoxBatchVar = QComboBox(self.ui)
        self.ui.comboBoxBatchVar.setEditable(False)
        self.ui.vlBatchVar.addWidget(self.ui.comboBoxBatchVar)

        ## Panel for numeric vars
        self.ui.comboBoxNumVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxNumVars.setEditable(False)
        self.ui.vlNumVars.addWidget(self.ui.comboBoxNumVars)

        ## Panel for cat vars
        self.ui.comboBoxCatVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxCatVars.setEditable(False)
        self.ui.vlCatVars.addWidget(self.ui.comboBoxCatVars)

        ## Panel for spline vars
        self.ui.comboBoxSplineVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxSplineVars.setEditable(False)
        self.ui.vlSplineVars.addWidget(self.ui.comboBoxSplineVars)

        ## Panel for ignore vars
        self.ui.comboBoxIgnoreVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxIgnoreVars.setEditable(False)
        self.ui.vlIgnoreVars.addWidget(self.ui.comboBoxIgnoreVars)

        ## Panel for target vars
        self.ui.comboBoxTargetVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxTargetVars.setEditable(False)
        self.ui.vlTargetVars.addWidget(self.ui.comboBoxTargetVars)

        ## Set default values for text fields
        self.placeholder_txt_var = '--var name--'
        
        self.ui.edit_outSuff.setPlaceholderText("_HARM")
        self.ui.edit_outMdlName.setPlaceholderText("harm_out_mdl1.pkl.gz")
        self.outdir = os.getcwd()

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()

        self.ui.edit_activeDset.setReadOnly(True)

        self.ui.wOptions.setMaximumWidth(300)
        
        ## Hide options in initial view
        self.selAction = ''
        self.ui.wParamsLearn.hide()
        self.ui.wParamsApply.hide()
        self.ui.wHarmonize.hide()

    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        self.ui.harmonizeBtn.clicked.connect(self.OnHarmonizeBtnClicked)
        self.ui.comboBoxAction.currentIndexChanged.connect(self.OnActionChanged)

        self.ui.selectModelBtn.clicked.connect(self.OnSelectModelBtnClicked)
        self.ui.outDirBtn.clicked.connect(self.OnOutDirBtnClicked)

    
    def OnActionChanged(self):
        
        logger.info('Harmonization action changed')

        self.selAction = self.ui.comboBoxAction.currentText()
        
        if self.selAction == 'LearnModel':
            self.ui.wParamsApply.hide()
            self.ui.wParamsLearn.show()
            self.ui.wHarmonize.show()
            

        if self.selAction == 'ApplyModel':
            self.ui.wParamsLearn.hide()
            self.ui.wParamsApply.show()

        self.statusbar.showMessage('Harmonization action changed: ' + self.selAction )

    def OnOutDirBtnClicked(self):

        #if self.dataPathLast == '':
            #directory = QtCore.QDir().homePath()
        #else:
            #directory = self.dataPathLast
        directory = QtCore.QDir().homePath()
        directory = '/home/guraylab/AIBIL/Github/NiChartPackages/NiChartHarmonize/test_temp/Test3/outputs'

        self.outdir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

    def OnSelectModelBtnClicked(self):

        #if self.dataPathLast == '':
            #directory = QtCore.QDir().homePath()
        #else:
            #directory = self.dataPathLast
        directory = QtCore.QDir().homePath()
        directory = '/home/guraylab/AIBIL/Github/NiChartPackages/NiChartHarmonize/test_temp/Test3/outputs/EXP2_ALL_TrainTest'

        filename = QtWidgets.QFileDialog.getOpenFileName(None,
            caption = 'Open model file',
            directory = directory,
            filter = "Pickle/pickle.gz files (*.pkl *.gz)")

        if filename[0] == "":
            logger.warning("No file was selected")
        else:
            self.modelname = filename[0]
            self.ui.wHarmonize.show()


    def OnHarmonizeBtnClicked(self):
        
        ## Read data
        df = self.data_model_arr.datasets[self.active_index].data

        if self.selAction == 'ApplyModel':
            ## Read args
            outSuff = self.ui.edit_outSuff.text()
            if outSuff == '':
                outSuff = '_HARM'
            if outSuff[0] == '_':
                outSuff = outSuff[1:]
            outCat = outSuff
            
            ## Apply Harmonization
            res_harm = nh_test.nh_harmonize_to_ref(df, self.modelname)
            
            if len(res_harm) == 1:          ## Model mismatch
                ## FIXME : not implemented yet
                logger.error('Harmonization model mismatch')

            else:
                mdlOut, dfOut = res_harm
            
            ## Set updated dset
            df = dfOut
            self.data_model_arr.datasets[self.active_index].data = df
            
            ## Load data to data view 
            self.dataView = QtWidgets.QTableView()

            ## Round values 
            ## FIXME this should be only in the view, not applied to data
            dfOut = dfOut.round(3)
            
            ## Add data to table
            self.PopulateTable(dfOut)
                                                                                                                            
            ## Set data view to mdi widget
            sub = QMdiSubWindow()
            sub.setWidget(self.dataView)
            sub.setWindowTitle('Harmonized Values')
            self.mdi.addSubWindow(sub)        
            sub.show()
            self.mdi.tileSubWindows()

        if self.selAction == 'LearnModel':
            ## Read args
            key_var = self.ui.comboBoxPrimaryKeyVar.currentText()
            batch_var = self.ui.comboBoxBatchVar.currentText()
            num_vars = self.ui.comboBoxNumVars.listCheckedItems()
            cat_vars = self.ui.comboBoxCatVars.listCheckedItems()
            spline_vars = self.ui.comboBoxSplineVars.listCheckedItems()
            ignore_vars = self.ui.comboBoxIgnoreVars.listCheckedItems()
            target_vars = self.ui.comboBoxTargetVars.listCheckedItems()
            out_model_file = os.path.join(self.outdir, self.ui.edit_outMdlName.text())

            ## Check args
            if key_var == self.placeholder_txt_var:
                logger.warning('Please select the primary key var ...')
                return

            if batch_var == self.placeholder_txt_var:
                logger.warning('Please select the batch var ...')
                return
        
            if len(target_vars) == 0:
                logger.warning('Target vars were not selected. Creates list of target vars automatically (all variables except primary key, batch var, covars and ignore vars)')
            
            nh_train.nh_learn_ref_model(df, key_var, batch_var, num_vars, cat_vars,
                                        spline_vars, ignore_vars, target_vars, False,
                                        out_model_file)
            
            
        

    def PopulateTable(self, data):
        
        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    # Add the values to comboBox
    def PopulateComboBox(self, cbox, values, strPlaceholder = None, bypassCheckable=False):
        cbox.blockSignals(True)
        cbox.clear()

        if bypassCheckable:
            cbox.addItemsNotCheckable(values)  ## The checkableqcombo for var categories
                                               ##   should not be checkable
        else:
            cbox.addItems(values)
            
        if strPlaceholder is not None:
            cbox.setCurrentIndex(-1)
            cbox.setEditable(True)
            cbox.setCurrentText(strPlaceholder)
        cbox.blockSignals(False)

    def OnDataChanged(self):
        
        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]
            colNames = dataset.data.columns.tolist()

            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ### Update combo boxes
            self.UpdatePanels(colNames)

    def UpdatePanels(self, colNames):
        
        self.PopulateComboBox(self.ui.comboBoxPrimaryKeyVar, colNames, self.placeholder_txt_var)
        self.PopulateComboBox(self.ui.comboBoxBatchVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxNumVars, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxCatVars, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSplineVars, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxIgnoreVars, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxTargetVars, colNames, '--var name--')



