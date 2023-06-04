from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox, QMessageBox
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

from NiChartGUI.core import datautils

import inspect

logger = iStagingLogger.get_logger(__name__)

class DistView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(DistView,self).__init__()

        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'distview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for X var
        self.ui.comboXVar = QComboBox(self.ui)
        self.ui.comboXVar.setEditable(False)
        self.ui.vlComboX.addWidget(self.ui.comboXVar)

        ## Panel for filter var
        self.ui.comboFilterVar = QComboBox(self.ui)
        self.ui.comboFilterVar.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboFilterVar)
        
        self.ui.comboFilterVal = CheckableQComboBox(self.ui)
        self.ui.comboFilterVal.setEditable(False)
        self.ui.vlComboFilterVal.addWidget(self.ui.comboFilterVal)

        ## Panel for hue var
        self.ui.comboHueVar = QComboBox(self.ui)
        self.ui.comboHueVar.setEditable(False)
        self.ui.vlComboHue.addWidget(self.ui.comboHueVar)

        self.ui.comboHueVal = CheckableQComboBox(self.ui)
        self.ui.comboHueVal.setEditable(False)
        self.ui.vlComboHueVal.addWidget(self.ui.comboHueVal)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()

        self.ui.wOptions.setMaximumWidth(300)

        self.ui.edit_activeDset.setReadOnly(True)       

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()


    def SetupConnections(self):

        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())

        self.ui.comboHueVar.currentIndexChanged.connect(lambda: self.OnHueIndexChanged())
        self.ui.comboFilterVar.currentIndexChanged.connect(lambda: self.OnFilterIndexChanged())

        self.ui.plotBtn.clicked.connect(lambda: self.OnPlotBtnClicked())

    def OnFilterIndexChanged(self):
        
        ## Threshold to show categorical values for selection
        TH_NUM_UNIQ = 20    
        
        selFilter = self.ui.comboFilterVar.currentText()
        selFilterVals = self.data_model_arr.datasets[self.active_index].data[selFilter].unique()
        
        if len(selFilterVals) < TH_NUM_UNIQ:
            self.ui.comboFilterVal.show()
            self.PopulateComboBox(self.ui.comboFilterVal, selFilterVals)
        else:
            print('Too many unique values for selection, skip : ' +  selFilter + ' ' + str(len(selFilterVals)))

    def OnHueIndexChanged(self):
        
        TH_NUM_UNIQ = 20
        
        selHue = self.ui.comboHueVar.currentText()
        selHueVals = self.data_model_arr.datasets[self.active_index].data[selHue].unique()
        
        if len(selHueVals) < TH_NUM_UNIQ:
            self.ui.comboHueVal.show()            
            self.PopulateComboBox(self.ui.comboHueVal, selHueVals)
        else:
            print('Too many unique values for selection, skip : ' + str(len(selHueVals)))

            
    #def PlotDist(self, axes, df, xVar, filterVar, filterVals, hueVar, hueVals):

        ## clear plot
        #axes.clear()

        ### Get data
        #colSel = [xVar]
        #if len(filterVals)>0:
            #colSel.append(filterVar)
        #if len(hueVals)>0:
            #colSel.append(hueVar)

        ### Remove duplicates in selected vars
        #colSel = [*set(colSel)]
        
        #dtmp = df[colSel]
        
        ### Filter data
        #if len(filterVals)>0:
            #dtmp = dtmp[dtmp[filterVar].isin(filterVals)]

        ### Get hue values
        #if len(hueVals)>0:
            #dtmp = dtmp[dtmp[hueVar].isin(hueVals)]

        ### Plot distribution
        #if len(hueVals)>0:
            #sns.kdeplot(data=dtmp, x=xVar, hue=hueVar, ax=axes)
        #else:
            #sns.kdeplot(data=dtmp, x=xVar, ax=axes)
        
        #sns.despine(fig=axes.get_figure(), trim=True)
        #axes.get_figure().set_tight_layout(True)
        #axes.set(xlabel=xVar)

    def OnPlotBtnClicked(self):

        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Read data
        df = self.data_model_arr.datasets[self.active_index].data
        
        ## Read user selections for the plot
        xVar = self.ui.comboXVar.currentText()
        hueVar = self.ui.comboHueVar.currentText()
        hueVals = self.ui.comboHueVal.listCheckedItems()
        filterVar = self.ui.comboFilterVar.currentText()
        filterVals = self.ui.comboFilterVal.listCheckedItems()
        if filterVals == []:
            filterVar = ''
        if hueVals == []:
            hueVar = ''
        
        ## Plot data    
        self.plotCanvas = PlotCanvas(self.ui)
        self.plotCanvas.axes = self.plotCanvas.fig.add_subplot(111)

        sub = QMdiSubWindow()
        sub.setWidget(self.plotCanvas)
        self.mdi.addSubWindow(sub)        
        
        #self.PlotDist(self.plotCanvas.axes, df, xVar, filterVar, filterVals, hueVar, hueVals)

        df_tmp = datautils.FilterData(df, xVar, filterVar, filterVals, hueVar, hueVals)
        datautils.PlotDist(self.plotCanvas.axes, df_tmp, xVar, hueVar)

        self.plotCanvas.draw()
        
        sub.show()
        self.mdi.tileSubWindows()

        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]       

        ## Add function definitons to notebook
        fCode = inspect.getsource(datautils.PlotDist).replace('(self, ','(').replace('self.','').replace('ax=axes','')
        self.cmds.add_funcdef('PlotDist', ['', fCode, ''])

        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Plot distribution')

        cmds.append('xVar = "' + xVar + '"')

        cmds.append('filterVar = "' + filterVar + '"')

        str_filterVals = '[' + ','.join('"{0}"'.format(x) for x in filterVals) + ']'
        cmds.append('filterVals = ' + str_filterVals)

        cmds.append('hueVar = "' + hueVar + '"')

        str_hueVals = '[' + ','.join('"{0}"'.format(x) for x in hueVals) + ']'
        cmds.append('hueVals = ' + str_hueVals)

        cmds.append('f, axes = plt.subplots(1, 1, figsize=(5, 4), dpi=100)')

        cmds.append('axes = PlotDist(axes, ' + dset_name + ', xVar, filterVar, filterVals, hueVar, hueVals)')
        
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------
        
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
        
        self.PopulateComboBox(self.ui.comboXVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboFilterVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboHueVar, colNames, '--var name--')
        
        self.ui.comboFilterVal.hide()
        self.ui.comboHueVal.hide()
        

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
        
    def PlotData2(self, xVar, filterVar, filterVals, hueVar, hueVals):

        #if filterVar == '':
            

        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        str_filterVals = ','.join('"{0}"'.format(x) for x in filterVals)
        str_hueVals = ','.join('"{0}"'.format(x) for x in hueVals)
        str_allVars = ','.join('"{0}"'.format(x) for x in [xVar, filterVar, hueVar])

        # clear plot
        self.plotCanvas.axes.clear()

        ## Get data
        dtmp = self.data_model_arr.datasets[self.active_index].data[[xVar, filterVar, hueVar]]
        
        ## Filter data
        if len(filterVals)>0:
            dtmp = dtmp[dtmp[filterVar].isin(filterVals)]

        ## Get hue values
        if len(hueVals)>0:
            dtmp = dtmp[dtmp[hueVar].isin(hueVals)]

        ## Get hue values
        if len(hueVals)>0:
            sns.kdeplot(data=dtmp, x=xVar, hue=hueVar, ax=self.plotCanvas.axes)
        else:
            sns.kdeplot(data=dtmp, x=xVar, ax=self.plotCanvas.axes)
        
        sns.despine(fig=self.plotCanvas.axes.get_figure(), trim=True)
        self.plotCanvas.axes.get_figure().set_tight_layout(True)
        
        self.plotCanvas.axes.set(xlabel=xVar)
        #self.plotCanvas.axes.set(ylabel=yVar)

        # refresh canvas
        self.plotCanvas.draw()


        ####################################################
        ## Populate commands that will be written in a notebook
        plot_cmds = []
        plot_cmds.append('DTMP = ' + dset_name + '[[' + str_allVars + ']]')
        if len(filterVals)>0:
            plot_cmds.append('DTMP = DTMP[DTMP' + '["' + filterVar + '"].isin([' + str_filterVals + '])]')
        if len(hueVals)>0:
            plot_cmds.append('DTMP = DTMP[DTMP' + '["' + hueVar + '"].isin([' + str_hueVals + '])]')
        if len(hueVals)>0:
            plot_cmds.append('sns.kdeplot(data=DTMP, x="' + xVar + '", hue="' + hueVar + '")')
        else:
            plot_cmds.append('sns.kdeplot(data=DTMP, x="' + xVar + '")')
        plot_cmds.append('plt.show()')        
        return plot_cmds

