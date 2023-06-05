import sys, os
import pandas as pd
import numpy as np
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox, QLayout
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
        
        ## Panel for action
        self.ui.comboAction = QComboBox(self.ui)
        self.ui.comboAction.setEditable(False)
        self.ui.vlAction.addWidget(self.ui.comboAction)
        self.PopulateComboBox(self.ui.comboAction, ['Show Table', 'Show Stats', 'Sort', 'Select', 
                                                    'Filter', 'Drop', 'Show Stats'], '--action--')        
        
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

        ## Options panel is not shown initially 
        ## Shown when a dataset is loaded

        ## Panel are shown based on selected actions
        

        self.ui.wShowTable.hide()
        #self.ui.wShowStats.hide()
        self.ui.wSort.hide()
        self.ui.wFilter.hide()
        #self.ui.wSelect.hide()
        #self.ui.wDrop.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        
        self.ui.edit_fname.setReadOnly(True)
        self.ui.edit_fname.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")

        self.ui.edit_dshape.setReadOnly(True)
        self.ui.edit_dshape.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")
        
        self.ui.wOptions.hide()
    
    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)

        self.ui.showTableBtn.clicked.connect(self.ShowTable)
        #self.ui.showStatsBtn.clicked.connect(self.ShowTable)
        self.ui.sortBtn.clicked.connect(self.OnSortBtnClicked)
        self.ui.filterBtn.clicked.connect(self.OnFilterBtnClicked)
        
        self.ui.comboBoxDsets.currentIndexChanged.connect(self.OnDataSelectionChanged)
        self.ui.comboBoxSortCat1.currentIndexChanged.connect(self.OnSortCat1Changed)
        self.ui.comboBoxSortCat2.currentIndexChanged.connect(self.OnSortCat2Changed)

        self.ui.comboAction.currentIndexChanged.connect(self.OnActionChanged)
        self.ui.comboBoxFilterVar.currentIndexChanged.connect(self.OnFilterVarChanged)
        

    def OnActionChanged(self):
        
        logger.info('Action changed')

        self.ui.wShowTable.hide()
        #self.ui.wShowStats.hide()
        self.ui.wSort.hide()
        #self.ui.wFilter.hide()
        #self.ui.wSelect.hide()
        #self.ui.wDrop.hide()

        self.selAction = self.ui.comboAction.currentText()

        if self.selAction == 'Show Table':
            self.ui.wShowTable.show()
        
        if self.selAction == 'Sort':
            self.ui.wSort.show()

        if self.selAction == 'Filter':
            self.ui.wFilter.show()

        if self.selAction == 'Select':
            logger.warning('ECLEC')
                
        
        #if self.selAction == '':
            #self.ui.wVars.show()
            #self.ui.wYVar.show()
            #self.ui.wPlotBtn.show()
            

        #if self.selAction == 'DistPlot':
            #self.ui.wVars.show()
            #self.ui.wYVar.hide()
            #self.ui.wPlotBtn.show()

        self.statusbar.showMessage('Action selection changed: ' + self.selAction)

    def OnSortBtnClicked(self):

        ## Read data and user selection
        dset_name = self.data_model_arr.dataset_names[self.active_index]
        dset_fname = self.data_model_arr.datasets[self.active_index].file_name
        df = self.data_model_arr.datasets[self.active_index].data
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

        ## Sort data
        dfSort = SortData(df, sortCols, sortOrders)

        ## Update data
        self.data_model_arr.datasets[self.active_index].data = dfSort
            
        ## Display status
        self.statusbar.showMessage('Sorted dataset')
        
        ##-------
        ## Populate commands that will be written in a notebook

        ## Add sort function definiton to notebook
        fCode = inspect.getsource(SortData).replace('(self, ','(')
        self.cmds.add_funcdef('SortData', ['', fCode, ''])

        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Sort dataset')

        str_sortCols = '[' +  ','.join('"{0}"'.format(x) for x in sortCols) + ']'
        cmds.append('sortCols = ' + str_sortCols)

        str_sortOrders = '[' +  ','.join('{0}'.format(x) for x in sortOrders) + ']'
        cmds.append('sortOrders = ' + str_sortOrders)

        cmds.append(dset_name + ' = SortData(' + dset_name + ', ' + str_sortCols + ', ' + str_sortOrders + ')')

        self.cmds.add_cmd(cmds)
        ##-------

        ##-------
        ## Display the table
        self.ShowTable()

    def OnFilterVarChanged(self):
        
        ## Threshold to show categorical values for selection
        TH_NUM_UNIQ = 20
        
        selcol = self.ui.comboBoxFilterVar.currentText()
        dftmp = self.data_model_arr.datasets[self.active_index].data[selcol]
        is_numerical = pd.to_numeric(dftmp.dropna(), errors='coerce').notnull().all()
        
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
            val_uniq = dftmp.unique()
            num_uniq = len(val_uniq)

            ## Select values if #unique values for the field is less than set threshold
            if num_uniq <= TH_NUM_UNIQ:
                self.ui.wFilterNumerical.hide()
                self.ui.wFilterCategorical.show()
                self.PopulateComboBox(self.ui.comboBoxCategoricalVars, val_uniq)

    def OnFilterBtnClicked(self):

        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Filter data
        dtmp = self.data_model_arr.datasets[self.active_index].data
        if self.filter_column_type == 'NUM':
            fvar = self.ui.comboBoxFilterVar.currentText()
            vmin = float(self.ui.edit_minval.text())
            vmax = float(self.ui.edit_maxval.text())
            dtmp = dtmp[(dtmp[fvar]>=vmin) & (dtmp[fvar]<=vmax)]
        
        if self.filter_column_type == 'CAT':
            fvar = self.ui.comboBoxFilterVar.currentText()
            varr = self.ui.comboBoxCategoricalVars.listCheckedItems()
            str_varr = ','.join('"{0}"'.format(x) for x in varr)
            dtmp = dtmp[dtmp[fvar].isin(varr)]

        self.data_model_arr.datasets[self.active_index].data = dtmp

        self.dataView = QtWidgets.QTableView()

        ## Load data to data view (reduce data size to make the app run faster)
        tmpData = self.data_model_arr.datasets[self.active_index].data
        tmpData = tmpData.head(self.data_model_arr.TABLE_MAXROWS)
        self.PopulateTable(tmpData)

        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()

        ##-------
        ## Populate commands that will be written in a notebook
        cmds = ['']
        cmds.append('# Filter dataset')        
        if self.filter_column_type == 'NUM':
            filterTxt = '[(' + dset_name + '["' + fvar + '"] >= ' + str(vmin) + ') & (' + \
                        dset_name + '["' + fvar + '"] <= ' + str(vmax) + ')]'
        if self.filter_column_type == 'CAT':
            filterTxt = '[' + dset_name + '["' + fvar + '"].isin([' + str_varr + '])]'
        cmds.append(dset_name + ' = ' + dset_name + filterTxt)
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------

    def ShowTable(self):

        ## Read data and user selection
        dset_name = self.data_model_arr.dataset_names[self.active_index]
        dset_fname = self.data_model_arr.datasets[self.active_index].file_name
        df = self.data_model_arr.datasets[self.active_index].data
            
        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        
        ## Reduce data size to make the app run faster
        tmpData = self.data_model_arr.datasets[self.active_index].data
#        tmpData = tmpData.head(self.data_model_arr.TABLE_MAXROWS)
        tmpData = pd.concat( [tmpData.head(20), tmpData.tail(20)])

        self.PopulateTable(tmpData)

        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        sub.setWindowTitle(dset_name + ': ' + os.path.basename(dset_fname))
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
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar1, selVars)
        
        self.statusbar.showMessage('User selected data category: ' + selCat)        

    def OnSortCat2Changed(self):

        ## Read selected variable category, find variables in that category, add them to combo box
        selCat = self.ui.comboBoxSortCat2.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar2, selVars)

        self.statusbar.showMessage('User selected data category: ' + selCat)        

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
        
        #self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxFilterVar, colNames, '--var name--')
        #self.PopulateComboBox(self.ui.comboBoxSelDuplVar, colNames, '--var name--')

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

        self.statusbar.showMessage('Selected new dataset: ' + selDsetName)
        
    #def OnDataChanged(self):
        
        #if self.data_model_arr.active_index >= 0:
     
            ### Make options panel visible
            #self.ui.wOptions.show()
        
            ### Set fields for various options     
            #self.active_index = self.data_model_arr.active_index
                
            ### Get data variables
            #dataset = self.data_model_arr.datasets[self.active_index]
            #colNames = dataset.data.columns.tolist()

            #logger.info(self.active_index)
            
            ### Set active dset name
            #self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ### Update selection, sorting and drop duplicates panels
            #self.UpdatePanels(colNames)
        
