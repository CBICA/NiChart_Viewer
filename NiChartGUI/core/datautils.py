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
#from NiChartGUI.core.datautils import *

import statsmodels.formula.api as sm

logger = iStagingLogger.get_logger(__name__)

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

def FilterData(df, x_var, filter_var, filter_vals, hue_var, hue_vals):
    '''Filter
    '''

    ## Get filter values
    df_out = df.copy()
    if len(filter_vals)>0:
        df_out = df[df[filter_var].isin(filter_vals)]

    ## Get hue values
    if len(hue_vals)>0:
        df_out = df_out[df_out[hue_var].isin(hue_vals)]

    return df_out

def StatsData(df, group_vars, display_vars, stat_vars):
    '''Stats
    '''
    ## Check validity of out vars and stats to display
    if len(display_vars) == 0:
        out_code = 1
        out_msg = 'WARNING: Input variable(s) not selected!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    if len(stat_vars) == 0:
        out_code = 2
        out_msg = 'WARNING: Input stat variable(s) not selected!'
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
    out_msg = 'SUCCESS: Created data stats'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}


def PlotDist(axes, df, x_var, hue_var):
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

def PlotData(axes, df, x_var, y_var, hue_var):
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
    
def SortData(df, sort_cols, sort_orders):
    '''Sort
    '''
    if len(sort_cols) == 0:
        out_code = 1        
        out_msg = 'WARNING: Sort variable(s) not selected!'
        return {'out_code' : out_code, 'out_msg' : out_msg}
    
    df_out = df.sort_values(sort_cols, ascending=sort_orders)
    
    out_code = 0
    out_msg = 'SUCCESS: Created sorted data'
    return {'out_code' : out_code, 'out_msg' : out_msg, 'df_out' : df_out}
    
    
def MergeData(df1, df2, mergeOn1, mergeOn2):
    '''Merge datasets
    '''
    dfOut = df1.merge(df2, left_on = mergeOn1, right_on = mergeOn2, suffixes=['','_DUPLVARINDF2'])
    
    ## If there are additional vars with the same name, we keep only the ones from the first dataset
    dfOut = dfOut[dfOut.columns[dfOut.columns.str.contains('_DUPLVARINDF2')==False]]
    
    return dfOut

def ConcatData(df1, df2):
    '''Merge datasets
    '''
    dfOut = pd.concat([df1, df2])
    
    return dfOut

def AdjCov(df, outVars, covCorrVars, covKeepVars=[], selCol='', selVals=[], outSuff='_COVADJ'):       
    '''Apply a linear regression model and correct for covariates
    It runs independently for each outcome variable
    The estimation is done on the selected subset and then applied to all samples
    The user can indicate covariates that will be corrected and not
    '''

    cmds = ['']
    
    # Combine covariates (to keep + to correct)
    if covKeepVars is []:
        covList = covCorrVars;
        isCorr = list(np.ones(len(covCorrVars)).astype(int))
    else:
        covList = covKeepVars + covCorrVars;
        isCorr = list(np.zeros(len(covKeepVars)).astype(int)) + list(np.ones(len(covCorrVars)).astype(int))
    
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
        dfOut = pd.concat([df[outVars], dfCovs], axis=1)
        dfTrain = dfOut
    else:
        dfOut = pd.concat([df[[selCol] + outVars], dfCovs], axis=1)
        dfTrain = dfOut[dfOut[selCol].isin(selVals)]
        
    ## Fit and apply model for each outcome var
    outVarNames = []
    for i, tmpOutVar in enumerate(outVars):

        ## Fit model
        str_model = tmpOutVar + '  ~ ' + str_covVars
        mod = sm.ols(str_model, data=dfTrain)
        res = mod.fit()

        ## Apply model
        corrVal = dfOut[tmpOutVar]
        for j, tmpCovVar in enumerate(covVars):
            if isCorrArr[j] == 1:
                corrVal = corrVal - df[tmpCovVar] * res.params[tmpCovVar]
        dfOut[tmpOutVar + outSuff] = corrVal
        outVarNames.append(tmpOutVar + outSuff)
    return dfOut, outVarNames


## Normalize data by the given variable
def NormalizeData(df, selVars, normVar, outSuff):
    dfNorm = 100 * df[selVars].div(df[normVar], axis=0)
    dfNorm = dfNorm.add_suffix(outSuff)
    outVarNames = dfNorm.columns.tolist()
    dfOut = pd.concat([df, dfNorm], axis=1)        
    return dfOut, outVarNames

    


