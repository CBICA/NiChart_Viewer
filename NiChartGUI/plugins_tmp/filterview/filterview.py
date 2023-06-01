from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QLineEdit, QComboBox, QMenu, QAction, QWidgetAction
import sys, os
import pandas as pd
from NiChartGUI.core.dataio import DataIO
# import dtale
from NiChartGUI.core.baseplugin import BasePlugin
from NiChartGUI.core import iStagingLogger
from NiChartGUI.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChartGUI.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChartGUI.core.gui.NestedQMenu import NestedQMenu
from NiChartGUI.core.model.datamodel import PandasModel

logger = iStagingLogger.get_logger(__name__)

class FilterView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(FilterView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None        
        
        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'filterview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Panel for variable selection
        self.ui.comboBoxSelCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelCat.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelCat)
        #self.ui.comboBoxSelCat.hide()

        self.ui.comboBoxSelVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)

        ## Panel for data filtering
        self.ui.comboBoxFilterCat = QComboBox(self.ui)
        self.ui.comboBoxFilterCat.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboBoxFilterCat)
        #self.ui.comboBoxFilterCat.hide()

        self.ui.comboBoxFilterVar = QComboBox(self.ui)
        self.ui.comboBoxFilterVar.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboBoxFilterVar)

        self.ui.comboBoxCategoricalVars = CheckableQComboBox(self.ui)
        self.ui.comboBoxCategoricalVars.setEditable(False)
        self.ui.hlFilterCat.addWidget(self.ui.comboBoxCategoricalVars)

        self.ui.wFilterNumerical.hide()
        self.ui.wFilterCategorical.hide()

        ## Panel for drop duplicates
        self.ui.comboBoxSelDuplCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelDuplCat.setEditable(False)
        self.ui.vlComboSelDupl.addWidget(self.ui.comboBoxSelDuplCat)
        self.ui.comboBoxSelDuplCat.hide()

        self.ui.comboBoxSelDuplVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelDuplVar.setEditable(False)
        self.ui.vlComboSelDupl.addWidget(self.ui.comboBoxSelDuplVar)
        
        
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        
        self.ui.edit_activeDset.setReadOnly(True)       
        
        ## Type of filter column (numeric or categorical)
        self.filter_column_type = None

    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        
        self.ui.selColBtn.clicked.connect(self.OnSelColBtnClicked)
        self.ui.filterBtn.clicked.connect(self.OnFilterBtnClicked)
        self.ui.dropBtn.clicked.connect(self.OnDropBtnClicked)

        self.ui.comboBoxFilterVar.currentIndexChanged.connect(self.OnFilterVarChanged)
        self.ui.comboBoxFilterCat.currentIndexChanged.connect(self.OnFilterCatChanged)

        self.ui.comboBoxSelCat.view().pressed.connect(self.OnSelCatSelected)
        self.ui.comboBoxSelDuplCat.view().pressed.connect(self.OnSelDuplCatSelected)

        ## https://gist.github.com/ales-erjavec/7624dd1d183dfbfb3354600b285abb94

    def OnFilterCatChanged(self):
        selCat = self.ui.comboBoxFilterCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxFilterVar, selVars)


    def OnSelDuplCatSelected(self, index):
        
        selItem = self.ui.comboBoxSelDuplCat.model().itemFromIndex(index) 
        
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
            self.ui.comboBoxSelDuplVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxSelDuplVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)
        
        #logger.info(checkedVars)


    def OnSelCatSelected(self, index):
        
        selItem = self.ui.comboBoxSelCat.model().itemFromIndex(index) 
        
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
            self.ui.comboBoxSelVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxSelVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)
        
        #logger.info(checkedVars)


    def OnDropBtnClicked(self):
        
        dset_name = self.data_model_arr.dataset_names[self.active_index]        


        selVars = self.ui.comboBoxSelDuplVar.listCheckedItems()

        str_selVars = ','.join('"{0}"'.format(x) for x in selVars)

        # Get active dset, apply drop, reassign it
        dtmp = self.data_model_arr.datasets[self.active_index].data   
        dtmp = dtmp.drop_duplicates(subset=selVars)
        self.data_model_arr.datasets[self.active_index].data = dtmp


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
        cmds.append('# Drop duplicates')        
        cmds.append(dset_name + ' = ' + dset_name + '.drop_duplicates(subset = [' + str_selVars + '])')
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------

    def OnSelColBtnClicked(self): 
        
        ## Get selected column names
        selVars = self.ui.comboBoxSelVar.listCheckedItems()
        str_selVars = ','.join('"{0}"'.format(x) for x in selVars)

        ## Select columns from dataset
        dtmp = self.data_model_arr.datasets[self.active_index].data      ## FIXME
        dtmp = dtmp[selVars]
        self.data_model_arr.datasets[self.active_index].data = dtmp
        
        ## Columns changed; Update data dictionary
        self.data_model_arr.datasets[self.active_index].UpdateDictSelCols(selVars)

        ## Show data table
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
        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        cmds = ['']
        cmds.append('# Select columns')                
        cmds.append(dset_name + ' = ' + dset_name + '[[' + str_selVars + ']]')
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
            catNames = dataset.data_cat_map.index.unique().tolist()

            logger.info(self.active_index)
            logger.info(catNames)
            
            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ## Update selection, sorting and drop duplicates panels
            self.UpdatePanels(catNames, colNames)

    def UpdatePanels(self, catNames, colNames):
        
        if len(catNames) == 1:      ## Single variable category, no need for category combobox
            self.ui.comboBoxSelCat.hide()
            self.ui.comboBoxFilterCat.hide()
            self.ui.comboBoxSelDuplCat.hide()
        else:
            self.ui.comboBoxSelCat.show()
            self.ui.comboBoxFilterCat.show()
            self.ui.comboBoxSelDuplCat.show()
            self.PopulateComboBox(self.ui.comboBoxSelCat, catNames, '--var group--', bypassCheckable=True)
            self.PopulateComboBox(self.ui.comboBoxFilterCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxSelDuplCat, catNames, '--var group--', bypassCheckable=True)
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxFilterVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSelDuplVar, colNames, '--var name--')
    

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
            
            
    

    
    
