from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox
import sys, os
import pandas as pd
from NiChartGUI.core.dataio import DataIO
# import dtale
from NiChartGUI.core.baseplugin import BasePlugin
from NiChartGUI.core import iStagingLogger
from NiChartGUI.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChartGUI.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChartGUI.core.plotcanvas import PlotCanvas
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
import statsmodels.formula.api as sm
from NiChartGUI.core.model.datamodel import PandasModel

import inspect

logger = iStagingLogger.get_logger(__name__)

class HarmonizeTrainView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(HarmonizeTrainView, self).__init__()

        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None

        self.TH_NUM_UNIQ = 20

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'harmonizetrainview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for action
        self.ui.comboBoxAction = CheckableQComboBox(self.ui)
        self.ui.comboBoxAction.setEditable(False)
        self.ui.vlAction.addWidget(self.ui.comboBoxAction)
        self.PopulateComboBox(self.ui.comboBoxAction, ['LearnModel', 'ApplyModel'])

        ## Panel for input data vars
        self.ui.comboBoxInDataVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxInDataVar.setEditable(False)
        self.ui.vlComboOut.addWidget(self.ui.comboBoxInDataVar)
        
        ## Panel for cov to keep
        self.ui.comboBoxCovKeepVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovKeepVar.setEditable(False)
        self.ui.vlComboCovKeep.addWidget(self.ui.comboBoxCovKeepVar)
        
        ## Panel for cov to correct
        self.ui.comboBoxCovCorrVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovCorrVar.setEditable(False)
        self.ui.vlComboCovCorr.addWidget(self.ui.comboBoxCovCorrVar)

        ## Panel for selection
        self.ui.comboBoxSelVar = QComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)

        self.ui.comboBoxSelVal = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVal.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVal)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()

        self.ui.edit_activeDset.setReadOnly(True)

        self.ui.wOptions.setMaximumWidth(300)
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())

        self.ui.comboBoxSelVar.currentIndexChanged.connect(lambda: self.OnSelIndexChanged())

        self.ui.adjCovBtn.clicked.connect(lambda: self.OnAdjCovBtnClicked())

    def CheckSelVars(self, selItem, comboVar):

        ## Read selected cat value
        selCat = selItem.text()

        ## Get list of cat to var name mapping
        dmap = self.data_model_arr.datasets[self.active_index].data_cat_map
        
        ## Check status of edit box for sel category
        isChecked = selItem.checkState()
        
        ## Set/reset check mark for selected var names in combobox for variables
        ## Update sel cat check box
        checkedVars = dmap.loc[[selCat]].VarName.tolist()
        
        if selItem.checkState() == QtCore.Qt.Checked: 
            comboVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            comboVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)

    ## Apply a linear regression model and correct for covariates
    ## It runs independently for each outcome variable
    ## The estimation is done on the selected subset and then applied to all samples
    ## The user can indicate covariates that will be corrected and not
    def AdjCov(self, df, inDataVars, covCorrVars, covKeepVars=[], selCol='', selVals=[], outSuff='_COVADJ'):       
        cmds = ['']
        
        # Make a copy of the init df
        # It will be modified to handle categorical vars
        dfOut = df.copy()
        
        # Combine covariates (to keep + to correct)
        if covKeepVars is []:
            covList = covCorrVars;
            isCorr = list(np.ones(len(covCorrVars)).astype(int))
        else:
            covList = covKeepVars + covCorrVars;
            isCorr = list(np.zeros(len(covKeepVars)).astype(int)) + list(np.ones(len(covCorrVars)).astype(int))
        str_covList = ' + '.join(covList)
        
        # Prep data
        TH_MAX_NUM_CAT = 20     ## FIXME: This should be a global var
        dfCovs = []
        isCorrArr = []
        for i, tmpVar in enumerate(covList):
            ## Detect if var is categorical
            is_num = pd.to_numeric(df[tmpVar].dropna(), errors='coerce').notnull().all()
            if df[tmpVar].unique().shape[0] < TH_MAX_NUM_CAT:
                is_num = False
            ## Create dummy vars for categorical data
            if is_num == False:
                dfDummy = pd.get_dummies(df[tmpVar], prefix=tmpVar, drop_first=True)
                dfCovs.append(dfDummy)
                isCorrArr = isCorrArr + list(np.zeros(dfDummy.shape[1]).astype(int)+isCorr[i])
            else:
                dfCovs.append(df[tmpVar])
                isCorrArr.append(isCorr[i])
        dfCovs = pd.concat(dfCovs, axis=1)
        
        ## Get cov names
        covVars = dfCovs.columns.tolist()
        str_covVars = ' + '.join(covVars)
        
        ## Get data with all vars
        df = pd.concat([df[inDataVars], dfCovs], axis=1)
        
        ## Select training dataset (regression parameters estimated from this set)
        if selVals == []:
            dfTrain = df
        else:
            dfTrain = df[df[selCol]==selVals]
            
        ## Fit and apply model for each outcome var
        outVarNames = []
        for i, tmpOutVar in enumerate(inDataVars):
            ## Fit model
            str_model = tmpOutVar + '  ~ ' + str_covVars
            mod = sm.ols(str_model, data=dfTrain)
            res = mod.fit()
            ## Apply model
            corrVal = df[tmpOutVar]
            for j, tmpCovVar in enumerate(covVars):
                if isCorrArr[j] == 1:
                    corrVal = corrVal - df[tmpCovVar] * res.params[tmpCovVar]
            dfOut[tmpOutVar + outSuff] = corrVal
            outVarNames.append(tmpOutVar + outSuff)
        return dfOut, outVarNames

    def OnAdjCovBtnClicked(self):
        
        ## Read data and user selection
        df = self.data_model_arr.datasets[self.active_index].data
        inDataVars = self.ui.comboBoxInDataVar.listCheckedItems()
        covKeepVars = self.ui.comboBoxCovKeepVar.listCheckedItems()
        covCorrVars = self.ui.comboBoxCovCorrVar.listCheckedItems()
        selCol = self.ui.comboBoxSelVar.currentText()
        selVals = self.ui.comboBoxSelVal.listCheckedItems()
        if selVals == []:
            selCol = ''
        outSuff = self.ui.edit_outSuff.text()
        if outSuff == '':
            outSuff = 'ADJCOV'
        if outSuff[0] == '_':
            outSuff = outSuff[1:]
        outCat = outSuff
        
        ## Correct data    
        dfCorr, outVarNames = self.AdjCov(df, inDataVars, covCorrVars, covKeepVars, selCol, selVals, outSuff)

        ## Set updated dset
        self.data_model_arr.datasets[self.active_index].data = dfCorr

        ## Create dict with info about new columns
        outDesc = 'Created by NiChartGUI AdjCovView Plugin'
        outSource = 'NiChartGUI AdjCovView Plugin'
        
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        

        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        
        ## Reduce data size to make the app run faster
        tmpData = self.data_model_arr.datasets[self.active_index].data
        tmpData = tmpData.head(self.data_model_arr.TABLE_MAXROWS)

        ## Show only columns involved in application
        tmpData = tmpData[outVarNames]
        
        self.PopulateTable(tmpData)
        
        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        
        ## Display status
        self.statusbar.showMessage('Displaying cov adjusted outcome variables')        

        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Add harmonizetrain function definiton to notebook
        fCode = inspect.getsource(self.AdjCov).replace('(self, ','(')
        self.cmds.add_funcdef('AdjCov', ['', fCode, ''])
        
        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Adj covariates')

        str_inDataVars = '[' + ','.join('"{0}"'.format(x) for x in inDataVars) + ']'
        cmds.append('inDataVars = ' + str_inDataVars)

        str_covCorrVars = '[' + ','.join('"{0}"'.format(x) for x in covCorrVars) + ']'
        cmds.append('covCorrVars = ' + str_covCorrVars)

        str_covKeepVars = '[' + ','.join('"{0}"'.format(x) for x in covKeepVars) + ']'
        cmds.append('covKeepVars = ' + str_covKeepVars)

        cmds.append('selCol  = "' + selCol + '"')

        str_selVals = '[' + ','.join('"{0}"'.format(x) for x in selVals) + ']'
        cmds.append('selVals = ' + str_selVals)
        
        cmds.append('outSuff  = "' + outSuff + '"')
        
        cmds.append(dset_name + ', outVarNames = AdjCov(' + dset_name + ', inDataVars, covCorrVars, covKeepVars, selCol, selVals, outSuff)')
        
        cmds.append(dset_name + '[outVarNames].head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------

    def PopulateTable(self, data):

        ### FIXME : Data is truncated to single precision for the display
        ### Add an option in settings to let the user change this
        data = data.round(1)

        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    def PopulateSelect(self):

        #get data column header names
        colNames = self.data_model_arr.datasets[self.active_index].data.columns.tolist()

        #add the list items to comboBox
        self.ui.comboBoxSelect.blockSignals(True)
        self.ui.comboBoxSelect.clear()
        self.ui.comboBoxSelect.addItems(colNames)
        self.ui.comboBoxSelect.blockSignals(False)

    def OnSelColChanged(self):
        
        ## Threshold to show categorical values for selection
        selcol = self.ui.comboBoxSelCol.currentText()
        dftmp = self.data_model_arr.datasets[self.active_index].data[selcol]
        val_uniq = dftmp.unique()
        num_uniq = len(val_uniq)

        self.ui.comboBoxSelVals.show()

        ## Select values if #unique values for the field is less than set threshold
        if num_uniq <= self.TH_NUM_UNIQ:
            #self.ui.wFilterNumerical.hide()
            #self.ui.wFilterCategorical.show()
            self.PopulateComboBox(self.ui.comboBoxSelVals, val_uniq)
        
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

    
    def OnSelIndexChanged(self):
        
        selCol = self.ui.comboBoxSelVar.currentText()
        selColVals = self.data_model_arr.datasets[self.active_index].data[selCol].unique()
        
        if len(selColVals) < self.TH_NUM_UNIQ:
            self.ui.comboBoxSelVal.show()
            self.PopulateComboBox(self.ui.comboBoxSelVal, selColVals)
        else:
            print('Too many unique values for selection, skip : ' + str(len(selColVals)))

    
    def OnDataChanged(self):
        
        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]
            colNames = dataset.data.columns.tolist()

            logger.info(self.active_index)
            
            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ## Update selection, sorting and drop duplicates panels
            self.UpdatePanels(colNames)

    def UpdatePanels(self, colNames):
        
        self.PopulateComboBox(self.ui.comboBoxInDataVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxCovKeepVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxCovCorrVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')

        self.ui.comboBoxSelVal.hide()


