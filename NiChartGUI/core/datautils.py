# This Python file uses the following encoding: utf-8
"""
contact: software@cbica.upenn.edu
Copyright (c) 2018 University of Pennsylvania. All rights reserved.
Use of this source code is governed by license located in license file: https://github.com/CBICA/NiChartGUI/blob/main/LICENSE
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
import numpy as np
import joblib
import os, sys
from NiChartGUI.core import iStagingLogger
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox, QLayout, QMessageBox, QErrorMessage

#from NiChartGUI.core.datautils import *

import statsmodels.formula.api as sm

logger = iStagingLogger.get_logger(__name__)

########################################################
## Plotting functions

def hue_regplot(data, x, y, hue, palette=None, **kwargs):
    '''Plotting
    '''
    regplots = []
    levels = data[hue].unique()
    if palette is None:
        default_colors = plt.colormaps['tab10']
        palette = {k: default_colors(i) for i, k in enumerate(levels)}
    legendhandls=[]
    for key in levels:
        regplots.append(sns.regplot(x=x, y=y, data=data[data[hue] == key], color=palette[key], **kwargs))
        legendhandls.append(Line2D([], [], color=palette[key], label=key))
    return (regplots, legendhandls)

def DataPlotDist(axes, df, x_var, hue_var):
    '''Plot
    '''

    # clear plot
    axes.clear()

    ## Plot distribution
    if len(hue_var)>0:
        sns.kdeplot(data=df, x=x_var, hue=hue_var, ax=axes)
    else:
        sns.kdeplot(data=df, x=x_var, ax=axes)
    sns.despine(fig=axes.get_figure(), trim=True)
    axes.get_figure().set_tight_layout(True)
    axes.set(xlabel=x_var)

def DataPlotScatter(axes, df, x_var, y_var, hue_var):
    '''Plot
    '''
    
    ## Get hue values
    if len(hue_var)>0:
        a,b = hue_regplot(df, x_var, y_var, hue_var, ax=axes)
        axes.legend(handles=b)
    else:
        sns.regplot(data = df, x = x_var, y = y_var, ax=axes)
    axes.yaxis.set_ticks_position('left')
    axes.xaxis.set_ticks_position('bottom')
    sns.despine(fig=axes.get_figure(), trim=True)
    axes.get_figure().set_tight_layout(True)
    axes.set(xlabel=x_var)
    axes.set(ylabel=y_var)
    
########################################################
## Data manipulation functions

def DataFilter(df, filter_var, filter_vals):
    '''Filter
    '''
    ## Get filter values
    if len(filter_var) == 0:
        out_code = 1
        out_msg = 'WARNING: Please select filter vars!'
        return {'out_code' : out_code, 'out_msg' : out_msg}

    is_numerical = pd.to_numeric(df[filter_var].dropna(), errors='coerce').notnull().all()

    if is_numerical:
        if len(filter_vals) != 2:
            out_code = 2
            out_msg = 'WARNING: Please select min / max values!'
            return {'out_code' : out_code, 'out_msg' : out_msg}
        df_out = df[ (df[filter_var] >= filter_vals[0]) & (df[filter_var] <= filter_vals[1])]
        
    else:
        if len(filter_vals) == 0:
            out_code = 3
            out_msg = 'WARNING: Please select filter values!'
            return {'out_code' : out_code, 'out_msg' : out_msg}
        df_out = df[df[filter_var].isin(filter_vals)]

    out_code = 0
    out_msg = 'Filtered data'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}

def DataSelectColumns(df, sel_cols):
    '''Select columns
    '''
    if len(sel_cols) == 0:
        out_code = 1
        out_msg = 'WARNING: Please select columns!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
        
    ## Select columns
    df_out = df[sel_cols]

    out_code = 0
    out_msg = 'Selected columns'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}

def DataGetStats(df, group_vars, display_vars, stat_vars):
    '''Stats
    '''
    ## Check validity of out vars and stats to display
    if len(display_vars) == 0:
        out_code = 1
        out_msg = 'WARNING: Please select input variable(s)!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    if len(stat_vars) == 0:
        out_code = 2
        out_msg = 'WARNING: Please select output stat(s)!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    df_out = df[group_vars + display_vars]
    
    if len(group_vars)>0:
        ## Get stats
        df_out = df_out.groupby(group_vars).describe()
        
        ## Select stats to display
        df_out = df_out.loc[:, pd.IndexSlice[:, stat_vars]]

        ## Change multiindex to single for display in table view
        df_out = df_out.reset_index()
        df_out = df_out.set_index(df_out.columns[0]).T
        df_out = df_out.reset_index(names = [group_vars[0], ''])

    else:
        ## Get stats
        df_out = df_out.describe()

        ## Select stats to display
        df_out = df_out.loc[stat_vars, :]

        ## Change multiindex to single for display in table view
        df_out = df_out.reset_index(names = 'Stats')

    out_code = 0
    out_msg = 'Created data stats'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}

def DataSort(df, sort_cols, sort_orders):
    '''Sort
    '''
    if len(sort_cols) == 0:
        out_code = 1        
        out_msg = 'WARNING: Please select sort column(s)!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    df_out = df.sort_values(sort_cols, ascending=sort_orders)
    
    out_code = 0
    out_msg = 'Created sorted data'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}
    
    
def DataMerge(df1, df2, mergeOn1, mergeOn2):
    '''Merge datasets
    '''
    dfOut = df1.merge(df2, left_on = mergeOn1, right_on = mergeOn2, suffixes=['','_DUPLVARINDF2'])
    
    ## If there are additional vars with the same name, we keep only the ones from the first dataset
    dfOut = dfOut[dfOut.columns[dfOut.columns.str.contains('_DUPLVARINDF2')==False]]
    
    return dfOut

def DataConcat(df1, df2):
    '''Merge datasets
    '''
    dfOut = pd.concat([df1, df2])
    
    return dfOut

def DataAdjCov(df, target_vars, cov_corr_vars, cov_keep_vars=[], 
               selCol='', selVals = [], out_suff = 'COVADJ'):       
    '''Apply a linear regression model and correct for covariates
    It runs independently for each outcome variable
    The estimation is done on the selected subset and then applied to all samples
    The user can indicate covariates that will be corrected and not
    '''
    # Combine covariates (to keep + to correct)
    if cov_keep_vars is []:
        covList = cov_corr_vars;
        isCorr = list(np.ones(len(cov_corr_vars)).astype(int))
    else:
        covList = cov_keep_vars + cov_corr_vars;
        isCorr = list(np.zeros(len(cov_keep_vars)).astype(int)) + list(np.ones(len(cov_corr_vars)).astype(int))

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
    if selVals == []:
        df_out = pd.concat([df[target_vars], dfCovs], axis=1)
        dfTrain = df_out
    else:
        df_out = pd.concat([df[[selCol] + target_vars], dfCovs], axis=1)
        dfTrain = df_out[df_out[selCol].isin(selVals)]
        
    ## Fit and apply model for each outcome var
    out_vars = []
    for i, tmpOutVar in enumerate(target_vars):

        ## Fit model
        str_model = tmpOutVar + '  ~ ' + str_covVars
        mod = sm.ols(str_model, data=dfTrain)
        res = mod.fit()

        ## Apply model
        corrVal = df_out[tmpOutVar]
        for j, tmpCovVar in enumerate(covVars):
            if isCorrArr[j] == 1:
                corrVal = corrVal - df[tmpCovVar] * res.params[tmpCovVar]
        df_out[tmpOutVar + '_' + out_suff] = corrVal
        out_vars.append(tmpOutVar + out_suff)
        
    out_code = 0
    out_msg = 'Created covariate adjusted data'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out, 'out_vars' : out_vars}
    
    return df_out, out_vars


## Normalize data by the given variable
def DataNormalize(df, sel_vars, norm_var, out_suff):
    '''Normalize data
    '''
    if len(sel_vars) == 0:
        out_code = 1        
        out_msg = 'WARNING: Please select column(s) to normalize!'
        return {'out_code' : out_code, 'out_msg' : out_msg}

    if norm_var == '':
        out_code = 2        
        out_msg = 'WARNING: Please select column to normalize by!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    df_out = 100 * df[sel_vars].div(df[norm_var], axis=0)
    df_out = df_out.add_suffix('_' + out_suff)
    out_vars = df_out.columns.tolist()
    df_out = pd.concat([df, df_out], axis=1)        

    out_code = 0
    out_msg = 'Created normalized data'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out, 'out_vars' : out_vars}


## Normalize data by the given variable
def DataDrop(df, sel_vars):
    '''Drop duplicates from data
    '''
    if len(sel_vars) == 0:
        out_code = 1        
        out_msg = 'WARNING: Please select variable(s)!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    df_out = df.drop_duplicates(subset = sel_vars)
    
    out_code = 0
    out_msg = 'Created data without duplicates'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}

########################################################
## Display widget functions

def WidgetShowTable(widget_in, df = None, dset_name = None):

    ## Read data and user selection
    if df is None:
        dset_name = widget_in.data_model_arr.dataset_names[widget_in.active_index]
        #dset_fname = widget_in.data_model_arr.datasets[widget_in.active_index].file_name
        df = widget_in.data_model_arr.datasets[widget_in.active_index].data
        
    ## Load data to data view 
    widget_in.dataView = QtWidgets.QTableView()
    
    ## Reduce data size to make the app run faster
    df_tmp = df.head(widget_in.data_model_arr.TABLE_MAXROWS)

    ## Round values for display
    df_tmp = df_tmp.applymap(lambda x: round(x, 2) if isinstance(x, (float, int)) else x)

    widget_in.PopulateTable(df_tmp)

    ## Set data view to mdi widget
    sub = QMdiSubWindow()
    sub.setWidget(widget_in.dataView)
    #sub.setWindowTitle(dset_name + ': ' + os.path.basename(dset_fname))
    sub.setWindowTitle(dset_name)
    widget_in.mdi.addSubWindow(sub)        
    sub.show()
    widget_in.mdi.tileSubWindows()

    ##-------
    ## Populate commands that will be written in a notebook

    ## Add cmds 
    cmds = ['']
    cmds.append('# Show dataset')
    cmds.append(dset_name + '.head()')
    cmds.append('')
    widget_in.cmds.add_cmd(cmds)
    ##-------

