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

    return df_out


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
    
    if len(sort_cols)>0:
        dfSort = df.sort_values(sort_cols, ascending=sort_orders)
        return dfSort
    else:
        return df
    
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

    
    
