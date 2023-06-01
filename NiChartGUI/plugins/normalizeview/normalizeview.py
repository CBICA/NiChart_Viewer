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

import inspect

logger = iStagingLogger.get_logger(__name__)

class NormalizeView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(NormalizeView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None        

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'normalizeview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Panel for Divide By
        self.ui.comboBoxDivideByVar = QComboBox(self.ui)
        self.ui.comboBoxDivideByVar.setEditable(False)
        self.ui.vlComboDivideBy.addWidget(self.ui.comboBoxDivideByVar)

        ## Panel for Apply To
        self.ui.comboBoxSelVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        self.ui.normalizeBtn.clicked.connect(self.OnNormalizeBtnClicked)


        ## https://gist.github.com/ales-erjavec/7624dd1d183dfbfb3354600b285abb94

    def PopulateTable(self, data):
        
        ### FIXME : Data is truncated to single precision for the display
        ### Add an option in settings to let the user change this
        data = data.round(1)

        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    #add the values to comboBox
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

            logger.info(self.active_index)
            
            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ## Update selection, sorting and drop duplicates panels
            self.UpdatePanels(colNames)

    def UpdatePanels(self, colNames):
        
        self.PopulateComboBox(self.ui.comboBoxDivideByVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')
    
    ## Normalize data by the given variable
    def NormalizeData(self, df, selVars, normVar, outSuff):
        dfNorm = 100 * df[selVars].div(df[normVar], axis=0)
        dfNorm = dfNorm.add_suffix(outSuff)
        outVarNames = dfNorm.columns.tolist()
        dfOut = pd.concat([df, dfNorm], axis=1)        
        return dfOut, outVarNames
    
    def OnNormalizeBtnClicked(self):
        
        ## Read normalize options
        normVar = self.ui.comboBoxDivideByVar.currentText()
        selVars = self.ui.comboBoxSelVar.listCheckedItems()
        outSuff = self.ui.edit_outSuff.text()
        if outSuff == '':
            outSuff = 'NORM'
        if outSuff[0] == '_':
            outSuff = outSuff[1:]
        outCat = outSuff

        ## Apply normalization
        df = self.data_model_arr.datasets[self.active_index].data
        dfNorm, outVarNames = self.NormalizeData(df, selVars, normVar, outSuff)

        ## Set updated dset
        self.data_model_arr.datasets[self.active_index].data = dfNorm
        
        ## Create dict with info about new columns
        outDesc = 'Created by NiChartGUI NormalizeView Plugin'
        outSource = 'NiChartGUI NormalizeView Plugin'
            
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
        self.statusbar.showMessage('Displaying normalized outcome variables')                

        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Add NormalizeData function definiton to notebook
        fCode = inspect.getsource(self.NormalizeData).replace('(self, ','(')
        self.cmds.add_funcdef('NormalizeData', ['', fCode, ''])
        
        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Normalize data')

        str_selVars = '[' + ','.join('"{0}"'.format(x) for x in selVars) + ']'
        cmds.append('selVars = ' + str_selVars)

        cmds.append('normVar = "' + normVar + '"')
        
        cmds.append('outSuff  = "' + outSuff + '"')
        
        cmds.append(dset_name + ', outVarNames = NormalizeData(' + dset_name + ', selVars, normVar, outSuff)')
        
        cmds.append(dset_name + '[outVarNames].head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------
   
    
