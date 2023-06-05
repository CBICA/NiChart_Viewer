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
        
        self.ui.wOptions.setMaximumWidth(300)
        
        self.ui.edit_fname.setReadOnly(True)
        self.ui.edit_fname.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")

        self.ui.edit_dshape.setReadOnly(True)
        self.ui.edit_dshape.setStyleSheet("border: 0px; background-color: rgb(235, 235, 245)")
        
        self.ui.wOptions.hide()
    
    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)

        self.ui.showTableBtn.clicked.connect(self.OnShowDataBtnClicked)
        self.ui.comboBoxDsets.currentIndexChanged.connect(self.OnDataSelectionChanged)
        self.ui.comboBoxSortCat1.currentIndexChanged.connect(self.OnSortCat1Changed)
        self.ui.comboBoxSortCat2.currentIndexChanged.connect(self.OnSortCat2Changed)

    def sortData(self, df, sortCols, sortOrders):
        if len(sortCols)>0:
            dfSort = df.sort_values(sortCols, ascending=sortOrders)
            return dfSort
        else:
            return df

    def OnShowDataBtnClicked(self):

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
        dfSort = self.sortData(df, sortCols, sortOrders)

        ## Update data
        self.data_model_arr.datasets[self.active_index].data = dfSort
            
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

        ## Add sort function definiton to notebook
        fCode = inspect.getsource(self.sortData).replace('(self, ','(')
        self.cmds.add_funcdef('SortData', ['', fCode, ''])

        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Show dataset')

        str_sortCols = '[' +  ','.join('"{0}"'.format(x) for x in sortCols) + ']'
        cmds.append('sortCols = ' + str_sortCols)

        str_sortOrders = '[' +  ','.join('{0}'.format(x) for x in sortOrders) + ']'
        cmds.append('sortOrders = ' + str_sortOrders)

        cmds.append(dset_name + ' = sortData(' + dset_name + ', ' + str_sortCols + ', ' + str_sortOrders + ')')

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

        ## Make options panel visible
        self.ui.wOptions.show()

        if len(self.data_model_arr.datasets) == 0:
            self.ui.wActiveDset.hide()
            self.ui.wSorting.hide()
            self.ui.wShowData.hide()
        else:
            self.ui.wActiveDset.show()
            self.ui.wSorting.show()
            self.ui.wShowData.show()

        ## Set fields for various options
        self.active_index = self.data_model_arr.active_index
        if self.active_index >= 0:
            
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
            
            ## Update dataset selection
            self.PopulateComboBox(self.ui.comboBoxDsets, dataset_names, currTxt = dataset_names[self.active_index])

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
        
        
