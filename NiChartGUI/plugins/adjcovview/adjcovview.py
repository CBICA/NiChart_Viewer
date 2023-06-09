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
from NiChartGUI.core.model.datamodel import DataModel, DataModelArr, PandasModel

from NiChartGUI.core.datautils import *

import inspect

logger = iStagingLogger.get_logger(__name__)

class AdjCovView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(AdjCovView,self).__init__()

        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None

        self.TH_NUM_UNIQ = 20

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'adjcovview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for action
        self.ui.comboAction = QComboBox(self.ui)
        self.ui.comboAction.setEditable(False)
        self.ui.vlAction.addWidget(self.ui.comboAction)
        self.PopulateComboBox(self.ui.comboAction, ['Normalize Data', 'Adjust Data'], '--action--')        

        ## Panel for norm var
        self.ui.comboNormVar = QComboBox(self.ui)
        self.ui.comboNormVar.setEditable(False)
        self.ui.vlComboNormVar.addWidget(self.ui.comboNormVar)
        
        ## Panel for cov to keep
        self.ui.comboCovKeepVar = CheckableQComboBox(self.ui)
        self.ui.comboCovKeepVar.setEditable(False)
        self.ui.vlComboCovKeep.addWidget(self.ui.comboCovKeepVar)
        
        ## Panel for cov to correct
        self.ui.comboCovCorrVar = CheckableQComboBox(self.ui)
        self.ui.comboCovCorrVar.setEditable(False)
        self.ui.vlComboCovCorr.addWidget(self.ui.comboCovCorrVar)

        ## Panel for selection
        self.ui.comboSelVar = QComboBox(self.ui)
        self.ui.comboSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboSelVar)

        self.ui.comboSelVal = CheckableQComboBox(self.ui)
        self.ui.comboSelVal.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboSelVal)

        ## Panel for primary key
        self.ui.comboPrimaryKeyVar = QComboBox(self.ui)
        self.ui.comboPrimaryKeyVar.setEditable(False)
        self.ui.vlPrimaryKeyVar.addWidget(self.ui.comboPrimaryKeyVar)

        ## Panel for outcome vars
        self.ui.comboOutVar = CheckableQComboBox(self.ui)
        self.ui.comboOutVar.setEditable(False)
        self.ui.vlComboOut.addWidget(self.ui.comboOutVar)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wNormVars.hide()
        self.ui.wAdjustVars.hide()
        self.ui.wOutVars.hide()

        ## Default value in adj cov view is to create new dset (not to overwrite the active dset)
        self.ui.check_createnew.setCheckState(QtCore.Qt.Checked)

        self.ui.edit_activeDset.setReadOnly(True)

        self.ui.wOptions.setMaximumWidth(300)
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())

        self.ui.comboSelVar.currentIndexChanged.connect(lambda: self.OnSelIndexChanged())

        self.ui.normalizeBtn.clicked.connect(lambda: self.OnNormalizeBtnClicked())
        self.ui.adjustBtn.clicked.connect(lambda: self.OnAdjustBtnClicked())

        self.ui.comboAction.currentIndexChanged.connect(self.OnActionChanged)

    def OnActionChanged(self):
        
        logger.info('Action changed')

        self.ui.wNormVars.hide()
        self.ui.wAdjustVars.hide()
        self.ui.wOutVars.hide()

        self.selAction = self.ui.comboAction.currentText()

        if self.selAction == 'Normalize Data':
            self.ui.wNormVars.show()
            self.ui.wOutVars.show()
        
        if self.selAction == 'Adjust Data':
            self.ui.wAdjustVars.show()
            self.ui.wOutVars.show()
        
        self.statusbar.showMessage('Action selection changed: ' + self.selAction)


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


    def OnNormalizeBtnClicked(self):
        '''Function to normalize data
        '''
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Get user selections
        key_var = self.ui.comboPrimaryKeyVar.currentText()
        norm_var = self.ui.comboNormVar.currentText()
        out_vars = self.ui.comboOutVar.listCheckedItems()
        out_suff = self.ui.edit_out_suff.text()
        if out_suff == '':
            out_suff = 'NORM'
        if out_suff[0] == '_':
            out_suff = out_suff[1:]

        ## Calculate results
        res_tmp = DataNormalize(df, key_var, out_vars, norm_var, out_suff)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']
        out_vars = res_tmp['out_vars']

        ## Create new dataset or update current active dataset
        if self.ui.check_createnew.isChecked():
            dmodel = DataModel(df_out, dset_name + '_Normalized')
            self.data_model_arr.AddDataset(dmodel)
            self.data_model_arr.OnDataChanged()

        else:
            self.data_model_arr.datasets[self.active_index].data = df_out
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        
        
        ## Display the table
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)
        
        ##-------
        ## Populate commands that will be written in a notebook

        ## Add NormalizeData function definiton to notebook
        fCode = inspect.getsource(DataNormalize).replace('(self, ','(')
        self.cmds.add_funcdef('NormalizeData', ['', fCode, ''])
        
        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Normalize data')

        str_out_vars = '[' + ','.join('"{0}"'.format(x) for x in out_vars) + ']'
        cmds.append('out_vars = ' + str_out_vars)

        cmds.append('norm_var = "' + norm_var + '"')
        
        cmds.append('out_suff  = "' + out_suff + '"')
        
        cmds.append(dset_name + ', outVarNames = NormalizeData(' + dset_name + ', out_vars, norm_var, out_suff)')
        
        cmds.append(dset_name + '[outVarNames].head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        

    def OnAdjustBtnClicked(self):
        
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Get user selections
        key_var = self.ui.comboPrimaryKeyVar.currentText()
        out_vars = self.ui.comboOutVar.listCheckedItems()
        cov_keep_vars = self.ui.comboCovKeepVar.listCheckedItems()
        cov_corr_vars = self.ui.comboCovCorrVar.listCheckedItems()
        sel_col = self.ui.comboSelVar.currentText()
        sel_vals = self.ui.comboSelVal.listCheckedItems()
        if sel_vals == []:
            sel_col = ''
        out_suff = self.ui.edit_out_suff.text()
        if out_suff == '':
            out_suff = 'ADJCOV'
        if out_suff[0] == '_':
            out_suff = out_suff[1:]
        outCat = out_suff
        
        ## Calculate results
        res_tmp = DataAdjCov(df, key_var, out_vars, cov_corr_vars, cov_keep_vars, sel_col, 
                             sel_vals, out_suff)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']

        ## Create new dataset or update current active dataset
        if self.ui.check_createnew.isChecked():
            dmodel = DataModel(df_out, dset_name + '_CovAdjusted')
            self.data_model_arr.AddDataset(dmodel)
            self.data_model_arr.OnDataChanged()

        else:
            self.data_model_arr.datasets[self.active_index].data = df_out
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        
        
        ## Display the table
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)
        
        ##-------
        ## Populate commands that will be written in a notebook

        ## Add adjcov function definiton to notebook
        fCode = inspect.getsource(DataAdjCov).replace('(self, ','(')
        self.cmds.add_funcdef('AdjCov', ['', fCode, ''])
        
        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Adj covariates')

        str_out_vars = '[' + ','.join('"{0}"'.format(x) for x in out_vars) + ']'
        cmds.append('out_vars = ' + str_out_vars)

        str_cov_corr_vars = '[' + ','.join('"{0}"'.format(x) for x in cov_corr_vars) + ']'
        cmds.append('cov_corr_vars = ' + str_cov_corr_vars)

        str_cov_keep_vars = '[' + ','.join('"{0}"'.format(x) for x in cov_keep_vars) + ']'
        cmds.append('cov_keep_vars = ' + str_cov_keep_vars)

        cmds.append('sel_col  = "' + sel_col + '"')

        str_sel_vals = '[' + ','.join('"{0}"'.format(x) for x in sel_vals) + ']'
        cmds.append('sel_vals = ' + str_sel_vals)
        
        cmds.append('out_suff  = "' + out_suff + '"')
        
        cmds.append(dset_name + ', outVarNames = DataAdjCov(' + dset_name + ', out_vars, cov_corr_vars, cov_keep_vars, sel_col, sel_vals, out_suff)')
        
        cmds.append(dset_name + '[outVarNames].head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        
    def ShowTable(self, df = None, dset_name = None):

        ## Read data and user selection
        if df is None:
            dset_name = self.data_model_arr.dataset_names[self.active_index]
            #dset_fname = self.data_model_arr.datasets[self.active_index].file_name
            df = self.data_model_arr.datasets[self.active_index].data
            
        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        
        ## Reduce data size to make the app run faster
        df_tmp = df.head(self.data_model_arr.TABLE_MAXROWS)

        ## Round values for display
        df_tmp = df_tmp.applymap(lambda x: round(x, 2) if isinstance(x, (float, int)) else x)

        self.PopulateTable(df_tmp)

        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        #sub.setWindowTitle(dset_name + ': ' + os.path.basename(dset_fname))
        sub.setWindowTitle(dset_name)
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()

        ## Display status
        self.statusbar.showMessage('Displaying dataset')
        
        ##-------
        ## Populate commands that will be written in a notebook

        ## Add cmds 
        cmds = ['']
        cmds.append('# Show dataset')
        cmds.append(dset_name + '.head()')
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

        self.ui.comboSelVals.show()

        ## Select values if #unique values for the field is less than set threshold
        if num_uniq <= self.TH_NUM_UNIQ:
            #self.ui.wFilterNumerical.hide()
            #self.ui.wFilterCategorical.show()
            self.PopulateComboBox(self.ui.comboSelVals, val_uniq)
        
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
        
        sel_col = self.ui.comboSelVar.currentText()
        sel_colVals = self.data_model_arr.datasets[self.active_index].data[sel_col].unique()
        
        if len(sel_colVals) < self.TH_NUM_UNIQ:
            self.ui.comboSelVal.show()
            self.PopulateComboBox(self.ui.comboSelVal, sel_colVals)
        else:
            print('Too many unique values for selection, skip : ' + str(len(sel_colVals)))

    
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

        self.PopulateComboBox(self.ui.comboPrimaryKeyVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboOutVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboCovKeepVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboCovCorrVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboSelVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboNormVar, colNames, '--var name--')

        self.ui.comboSelVal.hide()


