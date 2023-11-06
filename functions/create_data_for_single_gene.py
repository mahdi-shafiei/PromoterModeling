# import statements
import os
import pickle
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
sys.path.insert(0, '../functions/')
import basal_model_calcs as bmc
import mRNA_ratios as mr
import parameter_optimization as po
import create_cAct_cInh_vals as cv
import interface_GAMS as iG


def create_data_for_gene(flags):
    # setup
    gene_figs = []
    eq_str = flags['eq_str']
    
    ############################################################
    # create mRNA ratios and MA values
    ############################################################
    df_name = flags['central_gene']+'_zerod'+str(flags['use_zerod_A_matrix'])+'_mRNA_ratios_and_MA_vals.csv'
    if not flags['force_rerun'] and os.path.exists('../data/saved_mRNA_ratios_MA_vals/'+df_name):
        ratios_df = pd.read_csv('../data/saved_mRNA_ratios_MA_vals/'+df_name, index_col = 0)
    else:
        ratios_df = mr.calculate_mRNA_ratios_and_MA_values(gene_to_act_inh_iMs[flags['central_gene']][0], gene_to_act_inh_iMs[flags['central_gene']][1], flags)
        ratios_df.to_csv('../data/saved_mRNA_ratios_MA_vals/'+df_name)
    if flags['sanity_plots']:
        # sanity check plot
        fig, axs = plt.subplots(1, 3, figsize = (10, 3))
        axs[0].hist(ratios_df.actual_mRNA_ratio)
        axs[0].set_title('mRNA ratio')
        axs[0].axvline(x = 1, c = 'k', ls = '--')
        axs[1].hist(ratios_df.MA_activator)
        axs[1].set_title('MA activator')
        axs[1].axvline(x = 0, c = 'k', ls = '--')
        axs[2].hist(ratios_df.MA_inhibitor)
        axs[2].set_title('MA_inhibitor')
        axs[2].axvline(x = 0, c = 'k', ls = '--')
        # add a big axes, hide frame
        fig.add_subplot(111, frameon=False)
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.grid(False)
        plt.ylabel('Count')
        gene_figs.append(fig)
        plt.close(fig)
    
    
    
    ############################################################
    # pick KdRNAPCrp value, limit cActivator and cInhibitor based on it
    ############################################################
    # load in calculator
    gene_grid_name = '../data/gene_grid_constants/'+flags['central_gene']+'.pkl'
    if flags['force_rerun'] or not os.path.exists(gene_grid_name):  
        # basal model calculations
        grid_constants = bmc.basal_values(grid_constants, eq_str, flags)

        # pick KdRNAPCrp
        po.create_shared_lambda_df(eq_str, grid_constants)
        grid_constants['KdRNAPCrp'] = po.pick_KdRNAPCrp(ratios_df, flags)

        # save off grid constants
        pickle_out = open(gene_grid_name, 'wb')
        pickle.dump(grid_constants, pickle_out)
        pickle_out.close()
    else:
        pickle_in = open(gene_grid_name, 'rb')
        grid_constants = pickle.load(pickle_in)
        pickle_in.close()
    if flags['sanity_plots']:
        # sanity check plot
        
        # loading / setup
        po.create_shared_lambda_df(eq_str, grid_constants)

        # if you get weird results here, look at egulonML/parameter_optimization/0_framework.ipynb
        # it does the same thing as the function with plots along the way
        # try adjusting the initial guess for the first optimization
        # that is line 74 of functions/parameter_optimization.py

        # however, it is a sanity check to see if these values are near-correct
        rat_vals = np.linspace(min(ratios_df['actual_mRNA_ratio'].values.flatten()), max(ratios_df['actual_mRNA_ratio'].values.flatten()), 1000)

        cInh_vals = [po.mRNA_cActivator_to_cInhibitor(rat_val, flags['base_cActivator_val'], grid_constants['KdRNAPCrp']) for rat_val in rat_vals]
        cAct_vals = [po.mRNA_cInhibitor_to_cActivator(rat_val, flags['base_cInhibitor_val'], grid_constants['KdRNAPCrp']) for rat_val in rat_vals]

        fig, axs = plt.subplots(1, 2, figsize = (8, 3))
        ax1 = axs[0]
        l1, = ax1.plot(rat_vals, cInh_vals)
        plt.xlabel('mRNA Ratio')
        ax1.set_ylabel('cInhibitor', color = 'blue')
        ax1.tick_params(axis = 'y', labelcolor = 'blue')
        ax2 = ax1.twinx()
        l2, = ax2.plot(rat_vals, cAct_vals, color = 'red')
        ax2.set_ylabel('cActivator', color = 'red')
        ax2.tick_params(axis = 'y', labelcolor = 'red')
        ax1.axhline(y = 0, ls = '--', c = 'k')
        ax1.axvline(x = 1, ls = '--', c = 'k')
        # let's rescale cInhibitor (ax1) so that 0 is at the same point
        m1, M1 = ax1.get_ylim()
        percent1_up = (0 - m1) / (M1 - m1)
        m2, M2 = ax2.get_ylim()
        percent2_up = (0 - m2) / (M2 - m2)

        if percent1_up < percent2_up:
            # zero is higher than it should, so adjust it down by lowering the min
            m1 = percent2_up * M1 / (percent2_up - 1)
            ax1.set_ylim(m1, M1)
        else:
            # zero is lower than it should, so adjust it up
            M1 = m1 - (m1 / percent2_up)
            ax1.set_ylim(m1, M1)

        ax1.set_title('cAct and cInh ranges assuming other = 0')

        if flags['auto_set_max_range']:
            flags['cActivator'] = [-2, math.log10((1+flags['additional_tolerance'])*max(cAct_vals))] # Uses a log10 range
            flags['cInhibitor'] = [-2, math.log10((1+flags['additional_tolerance'])*max(cInh_vals))] # Uses a log10 range

        # let's create a 2D heatmap version of this, colored by the mRNA ratio
        cInh_range = np.linspace(0, max(cInh_vals), 100)
        cAct_range = np.linspace(0, max(cAct_vals), 100)
        mRNA_vals = pd.DataFrame(index = cInh_range, columns = cAct_range)
        for cInh in mRNA_vals.index:
            for cAct in mRNA_vals.columns:
                mRNA_vals.loc[cInh][cAct] = po.cActivator_cInhibitor_to_mRNA(cAct, cInh, grid_constants['KdRNAPCrp'])
        mRNA_vals = mRNA_vals.T.astype(float)

        # Convert the cInh_range and cAct_range to meshgrids for plotting
        cInh, cAct = np.meshgrid(cInh_range, cAct_range)

        # Create the heatmap
        heatmap = axs[1].pcolormesh(cInh, cAct, mRNA_vals.values, shading='auto', cmap='viridis')
        plt.colorbar(heatmap, label='mRNA values')
        axs[1].set_xlabel('cInhibitor')
        axs[1].set_ylabel('cActivator')
        axs[1].set_title('2D Heatmap of mRNA values')
        plt.tight_layout()
        gene_figs.append(fig)
        plt.close(fig)
        
        
        
    
    
    ############################################################
    # determine cActivator and cInhibior values, and greedy
    ############################################################
    greedy_path = '../data/cAct_cInh_vals/'+flags['central_gene']+'_greedy.pkl'
    norm_path = '../data/cAct_cInh_vals/'+flags['central_gene']+'.pkl'
    if flags['force_rerun']:
        return_figs, greedy_cAct_cInh_df, cAct_cInh_df = cv.create_cAct_cInh_for_gene(ratios_df, grid_constants, eq_str, flags)
        if flags['run_greedy']:
            pickle_out = open(greedy_path, 'wb')
            pickle.dump(greedy_cAct_cInh_df, pickle_out)
            pickle_out.close()
            pickle_out = open(norm_path, 'wb')
            pickle.dump(cAct_cInh_df, pickle_out)
            pickle_out.close()
        else:
            pickle_out = open(norm_path, 'wb')
            pickle.dump(cAct_cInh_df, pickle_out)
            pickle_out.close()
    else:
        if flags['run_greedy'] and os.path.exists(norm_path):
            pickle_in = open(norm_path, 'rb')
            cAct_cInh_df = pickle.load(pickle_in)
            pickle_in.close()
        elif os.path.exists(norm_path) and os.path.exists(greedy_path):
            pickle_in = open(norm_path, 'rb')
            cAct_cInh_df = pickle.load(pickle_in)
            pickle_in.close()
            pickle_in = open(greedy_path, 'rb')
            greedy_cAct_cInh_df = pickle.load(pickle_in)
            pickle_in.close()
        else: # need to rerun
            return_figs, greedy_cAct_cInh_df, cAct_cInh_df = cv.create_cAct_cInh_for_gene(ratios_df, grid_constants, eq_str, flags)
            if flags['run_greedy']:
                pickle_out = open(greedy_path, 'wb')
                pickle.dump(greedy_cAct_cInh_df, pickle_out)
                pickle_out.close()
                pickle_out = open(norm_path, 'wb')
                pickle.dump(cAct_cInh_df, pickle_out)
                pickle_out.close()
            else:
                pickle_out = open(norm_path, 'wb')
                pickle.dump(cAct_cInh_df, pickle_out)
                pickle_out.close()
    for fig in return_figs:
        gene_figs.append(fig)
        
    return(gene_figs)