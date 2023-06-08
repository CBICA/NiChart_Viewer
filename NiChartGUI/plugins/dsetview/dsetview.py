import sys, os
import pandas as pd
import numpy as np
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox, QLayout, QMessageBox, QErrorMessage
from NiChartGUI.core.dataio import DataIO
from NiChartGUI.core.baseplugin import BasePlugin
from NiChartGUI.core import iStagingLogger
from NiChartGUI.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChartGUI.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChartGUI.core.plotcanvas import PlotCanvas
from NiChartGUI.core.model.datamodel import PandasModel

from NiChartGUI.core.datautils import *

import inspect

logger = iStagingLogger.get_logger(__name__)

class DsetView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        '''Initialize view
        '''
        super(DsetView,self).__init__()
        
        ## Array that keeps all datasets
        ## All plugins point to the same data_model_arr
        ## Initialized by the mainwindow during loading of plugin
        self.data_model_arr = None

        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None

        ## Array that keeps all commands (used in notebook creation)
        self.cmds = None
        
        ## Index of curr dataset
        self.active_index = -1

        ## Read path
        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        
        ## Load ui file
        self.ui = uic.loadUi(os.path.join(root, 'dsetview.ui'),self)
        
        ## Main view panel
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))

        ## Panel for dataset selection
        self.ui.comboBoxDsets = QComboBox(self.ui)
        self.ui.comboBoxDsets.setEditable(False)        
        self.ui.vlComboDSets.addWidget(self.ui.comboBoxDsets)
        
        ## Panel for actions
        self.ui.comboAction = QComboBox(self.ui)
        self.ui.comboAction.setEditable(False)
        self.ui.vlAction.addWidget(self.ui.comboAction)
        self.PopulateComboBox(self.ui.comboAction, ['Show Data', 'Show Stats', 'Sort Data', 
                                                    'Select Columns', 'Filter Data', 
                                                    'Drop Duplicates'], '--action--')        
        
        ## Panel for show stats
        self.ui.comboBoxStatsGroupVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxStatsGroupVar.setEditable(False)
        self.ui.vlComboStatsGroup.addWidget(self.ui.comboBoxStatsGroupVar)

        self.ui.comboBoxStatsIn = CheckableQComboBox(self.ui)
        self.ui.comboBoxStatsIn.setEditable(False)
        self.ui.vlComboStatsIn.addWidget(self.ui.comboBoxStatsIn)

        self.ui.comboBoxStatsOut = CheckableQComboBox(self.ui)
        self.ui.comboBoxStatsOut.setEditable(False)
        self.ui.vlComboStatsOut.addWidget(self.ui.comboBoxStatsOut)

        ## Panel for variable selection
        self.ui.comboBoxSelVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)
        
        ## Panel for data filtering
        self.ui.comboBoxFilterVar = QComboBox(self.ui)
        self.ui.comboBoxFilterVar.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboBoxFilterVar)
        
        self.ui.comboBoxCategoricalVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxCategoricalVars.setEditable(False)
        self.ui.hlFilterCat.addWidget(self.ui.comboBoxCategoricalVars)

        self.ui.wFilterNumerical.hide()
        self.ui.wFilterCategorical.hide()
        
        ## Panel for sorting
        self.ui.comboBoxSortCat1 = QComboBox(self.ui)
        self.ui.vlComboSort1.addWidget(self.ui.comboBoxSortCat1)
        self.ui.comboBoxSortCat1.setCurrentIndex(-1)
        
        self.ui.comboBoxSortVar1 = SearchableQComboBox(self.ui)
        self.ui.vlComboSort1.addWidget(self.ui.comboBoxSortVar1)

        self.ui.comboBoxSortCat2 = QComboBox(self.ui)
        self.ui.vlComboSort2.addWidget(self.ui.comboBoxSortCat2)

        self.ui.comboBoxSortVar2 = SearchableQComboBox(self.ui)
        self.ui.vlComboSort2.addWidget(self.ui.comboBoxSortVar2)       

        ## Panel for drop duplicates
        self.ui.comboBoxSelDuplVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelDuplVar.setEditable(False)
        self.ui.vlComboSelDupl.addWidget(self.ui.comboBoxSelDuplVar)

        ## Panels will be shown based on selected actions
        self.ui.wShowTable.hide()
        self.ui.wShowStats.hide()
        self.ui.wSort.hide()
        self.ui.wFilter.hide()
        self.ui.wSelectCol.hide()
        self.ui.wDrop.hide()
        
        ## Few edits to the view
        self.ui.wOptions.setMaximumWidth(300)
        self.ui.edit_fname.setReadOnly(True)
        self.ui.edit_fname.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")
        self.ui.edit_dshape.setReadOnly(True)
        self.ui.edit_dshape.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")
        self.ui.wOptions.hide()
    
    def SetupConnections(self):
        '''Connect user actions to specific functions
        '''
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)

        self.ui.showTableBtn.clicked.connect(self.OnShowTableBtnClicked)
        self.ui.showStatsBtn.clicked.connect(self.OnShowStatsBtnClicked)
        self.ui.sortBtn.clicked.connect(self.OnSortBtnClicked)
        self.ui.filterBtn.clicked.connect(self.OnFilterBtnClicked)
        self.ui.selColBtn.clicked.connect(self.OnSelColBtnClicked)
        self.ui.dropBtn.clicked.connect(self.OnDropBtnClicked)

        self.ui.comboBoxDsets.currentIndexChanged.connect(self.OnDataSelectionChanged)
        self.ui.comboBoxSortCat1.currentIndexChanged.connect(self.OnSortCat1Changed)
        self.ui.comboBoxSortCat2.currentIndexChanged.connect(self.OnSortCat2Changed)
        self.ui.comboAction.currentIndexChanged.connect(self.OnActionChanged)
        self.ui.comboBoxFilterVar.currentIndexChanged.connect(self.OnFilterVarChanged)

    def OnActionChanged(self):
        '''Function to handle new action selection
        '''
        ## Hide all panels
        self.ui.wShowTable.hide()
        self.ui.wShowStats.hide()
        self.ui.wSort.hide()
        self.ui.wFilter.hide()
        self.ui.wSelectCol.hide()
        self.ui.wDrop.hide()

        ## Show panel for the selected action
        self.selAction = self.ui.comboAction.currentText()
        if self.selAction == 'Show Data':
            self.ui.wShowTable.show()
        
        if self.selAction == 'Show Stats':
            self.ui.wShowStats.show()

        if self.selAction == 'Sort Data':
            self.ui.wSort.show()

        if self.selAction == 'Filter Data':
            self.ui.wFilter.show()

        if self.selAction == 'Select Columns':
            self.ui.wSelectCol.show()
                
        if self.selAction == 'Drop Duplicates':
            self.ui.wDrop.show()
        
        self.statusbar.showMessage('Action selected: ' + self.selAction, 2000)
        
    def OnShowTableBtnClicked(self):
        '''Function to handle show data action
        '''        
        ## Display data
        self.statusbar.showMessage('Displaying dataframe', 2000)        
        WidgetShowTable(self)
       
    def OnShowStatsBtnClicked(self):
        '''Function to handle show stats action 
        '''        
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data

        ## Get user selections
        groupVars = self.ui.comboBoxStatsGroupVar.listCheckedItems()
        str_groupVars = ','.join('"{0}"'.format(x) for x in groupVars)

        selVars = self.ui.comboBoxStatsIn.listCheckedItems()
        str_selVars = ','.join('"{0}"'.format(x) for x in selVars)

        statVars = self.ui.comboBoxStatsOut.listCheckedItems()
        str_statVars = ','.join('"{0}"'.format(x) for x in statVars)

        ## Calculate results
        res_tmp = DataGetStats(df, groupVars, selVars, statVars)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']
    
        ## Display results
        self.statusbar.showMessage('Displaying data stats', 2000)
        WidgetShowTable(self, df = df_out, dset_name = 'Data Stats')        


    def OnDropBtnClicked(self):
        '''Function to handle drop data action
        '''
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data   

        ## Get user selections
        selVars = self.ui.comboBoxSelDuplVar.listCheckedItems()
        str_selVars = ','.join('"{0}"'.format(x) for x in selVars)

        ## Calculate results
        res_tmp = DataDrop(df, selVars)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']
        df_out = df.drop_duplicates(subset=selVars)

        ## Update data
        self.data_model_arr.datasets[self.active_index].data = df_out

        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        

        ## Display results
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)

        ##-------
        ## Populate commands that will be written in a notebook
        cmds = ['']
        cmds.append('# Drop duplicates')        
        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        cmds.append(dset_name + ' = ' + dset_name + '.drop_duplicates(subset = [' + str_selVars + '])')
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------

    def OnSortBtnClicked(self):
        '''Function to handle sort data action
        '''
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data
        
        ## Get user selections
        sortCols = []
        sortOrders = []
        if self.ui.check_sort1.isChecked():
            sortCols.append(self.ui.comboBoxSortVar1.currentText())
            if self.ui.check_asc1.isChecked():
                sortOrders.append(True)
            else:   
                sortOrders.append(False)
        if self.ui.check_sort2.isChecked():
            sortCols.append(self.ui.comboBoxSortVar2.currentText())
            if self.ui.check_asc2.isChecked():
                sortOrders.append(True)
            else:
                sortOrders.append(False)

        ## Calculate results
        res_tmp = DataSort(df, sortCols, sortOrders)        
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']
    
        ## Update data
        self.data_model_arr.datasets[self.active_index].data = df_out
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        
        
        ## Display the table
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)

        ##-------
        ## Populate commands that will be written in a notebook

        ## Add sort function definiton to notebook
        fCode = inspect.getsource(DataSort).replace('(self, ','(')
        self.cmds.add_funcdef('DataSort', ['', fCode, ''])

        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Sort dataset')

        dset_name = self.data_model_arr.dataset_names[self.active_index]
        str_sortCols = '[' +  ','.join('"{0}"'.format(x) for x in sortCols) + ']'
        cmds.append('sortCols = ' + str_sortCols)

        str_sortOrders = '[' +  ','.join('{0}'.format(x) for x in sortOrders) + ']'
        cmds.append('sortOrders = ' + str_sortOrders)

        cmds.append(dset_name + ' = DataSort(' + dset_name + ', ' + str_sortCols + ', ' + str_sortOrders + ')')

        self.cmds.add_cmd(cmds)

    def OnFilterVarChanged(self):
        '''Select filter values
        '''
        
        ## Threshold to show categorical values for selection
        TH_NUM_UNIQ = 20

        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data

        ## Get user selections
        selcol = self.ui.comboBoxFilterVar.currentText()
        
        ## Detect if column is numeric
        is_numerical = pd.to_numeric(df[selcol].dropna(), errors='coerce').notnull().all()
        
        ## Set options according to data type
        if is_numerical:
            self.filter_column_type = 'NUM'
        else:
            self.filter_column_type = 'CAT'
        
        ## Filter for numeric data
        if self.filter_column_type == 'NUM':
            self.ui.wFilterCategorical.hide()
            self.ui.wFilterNumerical.show()

        ## Filter for non-numeric data
        if self.filter_column_type == 'CAT':
            val_uniq = df.unique()
            num_uniq = len(val_uniq)

            ## Select values if #unique values for the field is less than set threshold
            if num_uniq > TH_NUM_UNIQ:
                self.errmsg.showMessage('Selected column has too many categories, skipping')
                return;                
            self.ui.wFilterNumerical.hide()
            self.ui.wFilterCategorical.show()
            self.PopulateComboBox(self.ui.comboBoxCategoricalVars, val_uniq)

    def OnFilterBtnClicked(self):
        '''Function to handle filter data action
        '''
        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data

        ## Get user selections
        fvar = self.ui.comboBoxFilterVar.currentText()
        if len(fvar) == 0:
            self.errmsg.showMessage('Please select input var!')
            return;

        ## Get user selections
        if self.filter_column_type == 'NUM':
            vmin = float(self.ui.edit_minval.text())
            vmax = float(self.ui.edit_maxval.text())
            fvals = [vmin, vmax]
        
        if self.filter_column_type == 'CAT':
            fvals = self.ui.comboBoxCategoricalVars.listCheckedItems()
            str_fvals = ','.join('"{0}"'.format(x) for x in fvals)

        ## Calculate results
        res_tmp = DataFilter(df, fvar, fvals)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;
        df_out = res_tmp['df_out']
        
        ## Update data
        self.data_model_arr.datasets[self.active_index].data = df_out
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        
        
        ## Display the table
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)

        ##-------
        ## Populate commands that will be written in a notebook
        cmds = ['']
        cmds.append('# Filter dataset')        
        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        if self.filter_column_type == 'NUM':
            filterTxt = '[(' + dset_name + '["' + fvar + '"] >= ' + str(vmin) + ') & (' + \
                        dset_name + '["' + fvar + '"] <= ' + str(vmax) + ')]'
        if self.filter_column_type == 'CAT':
            filterTxt = '[' + dset_name + '["' + fvar + '"].isin([' + str_fvals + '])]'
        cmds.append(dset_name + ' = ' + dset_name + filterTxt)
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        
    def OnSelColBtnClicked(self): 

        ## Get data
        df = self.data_model_arr.datasets[self.active_index].data

        ## Get user selections
        selVars = self.ui.comboBoxSelVar.listCheckedItems()
        str_selVars = ','.join('"{0}"'.format(x) for x in selVars)

        ## Calculate results
        res_tmp = DataSelectColumns(df, selVars)
        if res_tmp['out_code'] != 0:
            self.errmsg.showMessage(res_tmp['out_msg'])
            return;    
        df_out = res_tmp['df_out']

        ## Update data
        self.data_model_arr.datasets[self.active_index].data = df_out
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()        
        
        ## Display the table
        self.statusbar.showMessage('Dataframe updated, size: ' + str(df_out.shape), 2000)          
        WidgetShowTable(self)
        
        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        cmds = ['']
        cmds.append('# Select columns')                
        cmds.append(dset_name + ' = ' + dset_name + '[[' + str_selVars + ']]')
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)


    def PopulateTable(self, data):
        
        ### FIXME : Data is truncated to single precision for the display
        ### Add an option in settings to let the user change this
        data = data.round(1)
        
        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    def PopulateComboBox(self, cbox, values, strPlaceholder = None, currTxt = None):
        cbox.blockSignals(True)
        cbox.clear()

        ## Add values to combo box
        cbox.addItems(values)
        
        ## Add a first row with placeholder text to the combo box
        if strPlaceholder is not None:
            cbox.setCurrentIndex(-1)
            cbox.setEditable(True)
            cbox.setCurrentText(strPlaceholder)
        
        ## Set the current text in the combo box
        if currTxt is not None:
            cbox.setCurrentText(currTxt)
        cbox.blockSignals(False)
        
    def OnSortCat1Changed(self):
        
        ## Read selected variable category, find variables in that category, add them to combo box
        selCat = self.ui.comboBoxSortCat1.currentText()
        df_tmp = self.data_model_arr.datasets[self.active_index]
        selVars = df_tmp.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar1, selVars)
        
        self.statusbar.showMessage('User selected data category: ' + selCat, 2000)        

    def OnSortCat2Changed(self):

        ## Read selected variable category, find variables in that category, add them to combo box
        selCat = self.ui.comboBoxSortCat2.currentText()
        df_tmp = self.data_model_arr.datasets[self.active_index]
        selVars = df_tmp.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar2, selVars)

        self.statusbar.showMessage('User selected data category: ' + selCat, 2000)        

    def OnDataChanged(self):
        
        logger.info('Data changed')

        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index

            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]
            colNames = dataset.data.columns.tolist()
            
            dsetFileName = dataset.file_name
            dsetShape = dataset.data.shape
            dataset_names = self.data_model_arr.dataset_names

            ## Set data info fields
            self.ui.edit_fname.setText(os.path.basename(dsetFileName))
            self.ui.edit_fname.setCursorPosition(0)
            
            self.ui.edit_dshape.setText(str(dsetShape))
            self.ui.edit_dshape.setCursorPosition(0)

            ## Update sorting panel
            self.UpdateSortingPanel(colNames)
            
            ## Update selection, filter and drop duplicates panels
            self.UpdatePanels(colNames)
            
            ## Update dataset selection
            self.PopulateComboBox(self.ui.comboBoxDsets, dataset_names, currTxt = dataset_names[self.active_index])

    def UpdatePanels(self, colNames):
        
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxFilterVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSelDuplVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxStatsIn, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxStatsGroupVar, colNames, '--var name--')
        
        statsVars = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
        self.PopulateComboBox(self.ui.comboBoxStatsOut, statsVars, '--stats--')

    def UpdateSortingPanel(self, colNames):
        
        ## Uncheck edit boxes
        self.ui.check_sort1.setChecked(False)
        self.ui.check_asc1.setChecked(False)
        self.ui.check_sort2.setChecked(False)
        self.ui.check_asc2.setChecked(False)
        
        self.ui.comboBoxSortCat1.hide()
        self.ui.comboBoxSortCat2.hide()

        self.PopulateComboBox(self.ui.comboBoxSortVar1, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSortVar2, colNames, '--var name--')

    def OnDataSelectionChanged(self):
        
        logger.info('Dataset selection changed')

        ## Set current dataset
        selDsetName = self.ui.comboBoxDsets.currentText()
        self.active_index = np.where(np.array(self.data_model_arr.dataset_names) == selDsetName)[0][0]
        self.data_model_arr.active_index = self.active_index
        
        self.data_model_arr.OnDataChanged()

        self.statusbar.showMessage('Selected new dataset: ' + selDsetName, 2000)
        
