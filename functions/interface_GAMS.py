# run GAMs, need to test, move to outside .py file
import subprocess
import os
import pandas as pd
import numpy as np
import pickle
import shutil
import platform
import itertools

iM_to_b_regulator = {
    'GlpR' : ['b3423'], 
    'DhaR/Mlc' : ['b1201', 'b1594'], 
    'ArgR' : ['b3237'], 
    'NarL' : ['b1221'], 
    'MalT' : ['b3418'], 
    'OxyR' : ['b3961'], 
    'Crp-2' : ['b3357'], 
    'AtoC' : ['b2220'], 
    'PurR-1' : ['b1658'], 
    'CsqR' : ['b3884'], 
    'MetJ' : ['b3938'], 
    'PurR-2' : ['b1658'], 
    'Cbl+CysB' : ['b1987' 'b1275'], 
    'GlcC' : ['b2980'], 
    'Crp-1' : ['b3357'], 
    'YiaJ' : ['b3574'], 
    'GcvA' : ['b2808'], 
    'XylR' : ['b3569'], 
    'RpoH' : ['b3461'], 
    'GadEWX' : ['b3512', 'b3515', 'b3516'], 
    'PrpR' : ['b0330'], 
    'GadWX' : ['b3516', 'b3515'], 
    'CecR' : ['b0796'], 
    'ArcA-1' : ['b4401'], 
    'Fnr' : ['b1334'], 
    'CdaR' : ['b0162'], 
    'Pyruvate' : ['b2125', 'b2381', 'b0113'], 
    'SrlR+GutM' : ['b2707', 'b2706'], 
    'NagC/TyrR' : ['b0676', 'b1323'], 
    'CpxR' : ['b3912'], 
    'Lrp' : ['b0889'], 
    'Leu/Ile' : ['b3773'], 
    'Fur-1' : ['b0683'], 
    'CysB' : ['b1275'], 
    'FliA' : ['b1922'], 
    'PuuR' : ['b1299'], 
    'NikR' : ['b3481'], 
    'NtrC+RpoN' : ['b3868', 'b3202'], 
    'RcsAB' : ['b1951', 'b2217'], 
    'Fur-2' : ['b0683'], 
    'Copper' : ['b0571', 'b1969', 'b0487'], 
    'AllR/AraC/FucR' : ['b0506', 'b0064', 'b2805'], 
    'Cra' : ['b0080'], 
    'ArcA-2' : ['b4401'], 
    'EvgA' : ['b2369'], 
    'Zinc' : ['b3292', 'b4046'], 
    'SoxS' : ['b4062'], 
    'Nac' : ['b1988'], 
    'Tryptophan' : ['b4393'], 
    'FadR/IclR' : ['b1187', 'b4018'], 
    'FlhDC' : ['b1892', 'b1891'], 
    'GntR/TyrR' : ['b3438', 'b1323'], 
    'RpoS' : ['b2741'], 
    'ExuR/FucR' : ['b3094', 'b2805'], 
    'FecI' : ['b4293'], 
    'RbsR' : ['b3753']
}


def run_GAMs(flags_df, TF_flags_df, stable_flags, promoter, inhibitor, cell_constants, GAMs_run_dir, parameter_flags = None):
    ############################################################
    # save input parameters
    ############################################################
    if not parameter_flags:
        parameter_flags = stable_flags
        baby_dict = {
            'act_TF_conc_lo' : parameter_flags['act_TF_conc_lo'],
            'act_TF_conc_up' : parameter_flags['act_TF_conc_up'],
            'act_Kd_lo' : parameter_flags['act_Kd_lo'],
            'act_Kd_up' : parameter_flags['act_Kd_up'],
            'inh_TF_conc_lo' : parameter_flags['inh_TF_conc_lo'],
            'inh_TF_conc_up' : parameter_flags['inh_TF_conc_up'],
            'inh_Kd_lo' : parameter_flags['inh_Kd_lo'],
            'inh_Kd_up' : parameter_flags['inh_Kd_up'],

            'weight_act_obj1' : parameter_flags['weight_act_obj1'],
            'weight_inh_obj1' : parameter_flags['weight_inh_obj1'],
            'weight_act_obj2' : parameter_flags['weight_act_obj2'],
            'weight_inh_obj2' : parameter_flags['weight_inh_obj2'],
            'weight_mRNA_match' : parameter_flags['weight_mRNA_match'],
            'weight_act_corr' : parameter_flags['weight_act_corr'],
            'weight_inh_corr' : parameter_flags['weight_inh_corr'],
            'act_metab_Total_lo' : parameter_flags['act_metab_Total_lo'],
            'act_metab_Total_up' : parameter_flags['act_metab_Total_up'],
            'inh_metab_Total_lo' : parameter_flags['inh_metab_Total_lo'],
            'inh_metab_Total_up' : parameter_flags['inh_metab_Total_up'],
        }
    else:
        para_sweep = ['act_TF_conc_lo', 'act_TF_conc_up', 'act_Kd_lo', 'act_Kd_up', 'inh_TF_conc_lo', 'inh_TF_conc_up', 'inh_Kd_lo', 'inh_Kd_up', 'weight_act_obj1', 'weight_inh_obj1', 'weight_act_obj2', 'weight_inh_obj2', 'weight_mRNA_match', 'weight_act_corr', 'weight_inh_corr', 'inh_metab_Total_lo', 'inh_metab_Total_up', 'act_metab_Total_lo', 'act_metab_Total_up']
        baby_dict = {}
        for para in para_sweep:
            if para in parameter_flags:
                baby_dict.update({para : parameter_flags[para]})

    if not promoter:
        # no promoter exists, so set the relative weights to zero so the model doesn't optimize for it
        baby_dict['weight_act_obj1'] = 0
        baby_dict['weight_act_obj2'] = 0
        baby_dict['weight_act_corr'] = 0
        # set cActivator to be the minimum value across all samples (I think zero is iffy with how the model is set up currently, so instead setting it to a very low value
        baby_dict['act_Kd_lo'] = stable_flags['act_Kd_up']
        baby_dict['act_TF_conc_up'] = 1e-25
        baby_dict['act_TF_conc_lo'] = 1e-25
    if not inhibitor:
        # no inhibitor exists, so set the relative weights to zero so the model doesn't optimize for it
        baby_dict['weight_inh_obj1'] = 0
        baby_dict['weight_inh_obj2'] = 0
        baby_dict['weight_inh_corr'] = 0
        # set cActivator to be the minimum value across all samples (I think zero is iffy with how the model is set up currently, so instead setting it to a very low value
        baby_dict['inh_Kd_lo'] = stable_flags['inh_Kd_up']
        baby_dict['inh_TF_conc_up'] = 1e-25
        baby_dict['inh_TF_conc_lo'] = 1e-25
    df = pd.DataFrame(list(baby_dict.items()), columns=['Parameter', 'Value']).set_index('Parameter')
    df.to_csv(GAMs_run_dir+'/input_files/parameters.csv')
    # now pull in TF specific parameters
    baby_dict = {
        'kd_act_metab' : 0,
        'kd_inh_metab' : 0,
    }
    if promoter:
        baby_dict.update({'kd_act_metab' : TF_flags_df.loc[promoter].values[0]})
    if inhibitor:
        baby_dict.update({'kd_inh_metab' : TF_flags_df.loc[inhibitor].values[1]})
    df = pd.DataFrame(list(baby_dict.items()), columns=['Parameter', 'Value']).set_index('Parameter')
    df.to_csv(GAMs_run_dir+'/input_files/input_constants.csv')
    
    
    ############################################################
    # create TF concentration
    ############################################################
    concentrations = pd.read_csv('../data/validation_data_sets/converted_log_tpm_in_M.csv', index_col = 0)
    
    # the above converts it into concentrations, but not
    
    if promoter:
        concentrations.loc[promoter].to_csv(GAMs_run_dir+'/input_files/exported_act_TF_conc.csv')
    else:
        # still need a dummy for this that isn't used
        concentrations.loc[inhibitor].to_csv(GAMs_run_dir+'/input_files/exported_act_TF_conc.csv')
    if inhibitor:
        concentrations.loc[inhibitor].to_csv(GAMs_run_dir+'/input_files/exported_inh_TF_conc.csv')
    else:
        # still need a dummy for this that isn't used
        concentrations.loc[promoter].to_csv(GAMs_run_dir+'/input_files/exported_inh_TF_conc.csv')

    
    # first let's merge together the files
    files_use = []
    if stable_flags['run_on_all']:
        files = os.listdir('../data/cAct_cInh_vals/')
        for f in files:
            gene_name = file.split('.')[0].split('_')[0]
            if stable_flags['use_greedy'] and 'greed' not in f: continue
            if not stable_flags['use_greedy'] and 'greed' in f: continue
            files_use.append(f)
    else:
        for sample in stable_flags['limit_samples']:
            use_zerod_A = flags_df.loc[sample]['use_zerod_A_matrix']
            if stable_flags['use_greedy']:
                f_name = sample+'_greedy.pkl'
            else:
                f_name = sample+'.pkl'
            if os.path.exists('../data/cAct_cInh_vals/'+f_name):
                files_use.append(f_name)
    if False: # old way
        if stable_flags['run_on_all']:
            files = os.listdir('../data/save_for_GAMs/')
            for f in files:
                gene_name = file.split('_')[0]
                use_zerod_A = flags_df.loc[gene_name]['use_zerod_A_matrix']
                if 'composite' in f: continue
                if 'zerod'+str(use_zerod_A) not in f: continue
                if stable_flags['use_greedy'] and 'non_greed' in f: continue
                if not stable_flags['use_greedy'] and 'non_greed' not in f: continue
                files_use.append(f)
        else:
            for sample in stable_flags['limit_samples']:
                use_zerod_A = flags_df.loc[sample]['use_zerod_A_matrix']
                if stable_flags['use_greedy']:
                    f_name = sample+'_zerod'+str(use_zerod_A)+'_cAct_cInh_vals.csv'
                else:
                    f_name = sample+'_non_greed_zerod'+str(use_zerod_A)+'_cAct_cInh_vals.csv'
                if os.path.exists('../data/save_for_GAMs/'+f_name):
                    files_use.append(f_name)
             
                
    for f in files_use:
        shared_indices = []
        first = True
        for file in files_use:
            gene_name = file.split('.')[0].split('_')[0]
            temp_df = pd.read_pickle('../data/cAct_cInh_vals/'+file)
            if first:
                shared_indices = set(temp_df.index)
                first = False
            else:
                shared_indices = set(shared_indices.intersection(set(temp_df.index)))
        shared_indices = list(shared_indices)
        shared_indices.sort()
        act_df = pd.DataFrame(index = shared_indices)
        inh_df = pd.DataFrame(index = shared_indices)
        for file in files_use:
            gene_name = file.split('.')[0].split('_')[0]
            act_df[gene_name] = pd.read_pickle('../data/cAct_cInh_vals/'+file)['cAct'].loc[act_df.index].values
            inh_df[gene_name] = pd.read_pickle('../data/cAct_cInh_vals/'+file)['cInh'].loc[inh_df.index].values
        
    act_df.to_csv(GAMs_run_dir+'/input_files/composite_cAct_vals.csv')
    inh_df.to_csv(GAMs_run_dir+'/input_files/composite_cInh_vals.csv')
    vals = []
    for col in act_df.columns:
        vals.append(max(act_df[col]))
    max_df = pd.DataFrame(vals, index = act_df.columns)
    max_df.to_csv(GAMs_run_dir+'/input_files/max_cActs.csv')
    vals = []
    for col in inh_df.columns:
        vals.append(max(inh_df[col]))
    max_df = pd.DataFrame(vals, index = inh_df.columns)
    max_df.to_csv(GAMs_run_dir+'/input_files/max_cInhs.csv')
    
    
    ############################################################
    # save actual ratio_df values
    ############################################################
    collection = []
    index = []
    for f in files_use:
        gene_name = f.split('.')[0].split('_')[0]
        use_zerod_A = flags_df.loc[gene_name]['use_zerod_A_matrix']
        df_name = gene_name+'_zerod'+str(use_zerod_A)+'_mRNA_ratios_and_MA_vals.csv'
        ratios_df = pd.read_csv('../data/saved_mRNA_ratios_MA_vals/'+df_name, index_col = 0)
        collection.append(ratios_df['actual_mRNA_ratio'])
        index.append(gene_name)
    ratios_combo_df = pd.DataFrame(collection, index = index)
    ratios_combo_df.T.to_csv(GAMs_run_dir+'/input_files/actual_mRNA_ratio.csv')
    

    ############################################################
    # create constants files for mRNA calculation
    ############################################################
    index = []
    collection = []
    for f in files_use:
        gene_name = f.split('.')[0].split('_')[0]
        gene_grid_name = '../data/gene_grid_constants/'+gene_name+'.pkl'
        pickle_in = open(gene_grid_name, 'rb')
        grid_constants = pickle.load(pickle_in)
        pickle_in.close()
        index.append(gene_name)
        collection.append(grid_constants)
    constants_df = pd.DataFrame(collection, index = index)
    constants_df.T.to_csv(GAMs_run_dir+'/input_files/grid_constants.csv')     
    # make sample_constants file, for now just contains RNAP conc
    RNAP_conc_df = pd.read_csv('../data/RNAP_conc.csv', index_col = 0)
    RNAP_conc_df = RNAP_conc_df.loc[ratios_df.index]
    RNAP_conc_df.T.to_csv(GAMs_run_dir+'/input_files/sample_constants.csv')     
    
    
    ############################################################
    # run GAMS
    ############################################################
    # remove old results
    if stable_flags['delete_old']:
        if os.path.exists('../data/GAMS_output/cInh_Kd_results.csv'):
            os.remove('../data/GAMS_output/cInh_Kd_results.csv')
        if os.path.exists('../data/GAMS_output/cInh_TF_conc_results.csv'):
            os.remove('../data/GAMS_output/cInh_TF_conc_results.csv')
        if os.path.exists('../data/GAMS_output/cAct_Kd_results.csv'):
            os.remove('../data/GAMS_output/cAct_Kd_results.csv')
        if os.path.exists('../data/GAMS_output/cAct_TF_conc_results.csv'):
            os.remove('../data/GAMS_output/cAct_TF_conc_results.csv')

    # call GAMS
    shutil.copyfile('../GAMs/conopt.opt', GAMs_run_dir+'/conopt.opt')
    if platform.system() == 'Windows':
        gams_loc =  r'"C:\GAMS\win64\28.2\gams.exe"' # zzz shouldn't be hard set like this, but for now this is fine
        if stable_flags['run_seperate']:
            print('a')
            shutil.copyfile('../GAMs/cAct_model.gms', GAMs_run_dir+'/cAct_model.gms')
            shutil.copyfile('../GAMs/cInh_model.gms', GAMs_run_dir+'/cInh_model.gms')
            _ = subprocess.call(gams_loc+' cAct_model.gms', shell = True, cwd = GAMs_run_dir)
            _ = subprocess.call(gams_loc+' cInh_model.gms', shell = True, cwd = GAMs_run_dir)
        elif inhibitor and not promoter:
            shutil.copyfile('../GAMs/model_inhibitor_metab_complimentary.gms', GAMs_run_dir+'/combined_model.gms')
            _ = subprocess.call(gams_loc+' combined_model.gms', cwd = GAMs_run_dir, shell=True)
        elif promoter and not inhibitor:
            shutil.copyfile('../GAMs/model_activator_metab_complimentary.gms', GAMs_run_dir+'/combined_model.gms')
            _ = subprocess.call(gams_loc+' combined_model.gms', cwd = GAMs_run_dir, shell=True)
        else:
            shutil.copyfile('../GAMs/combined_model.gms', GAMs_run_dir+'/combined_model.gms')
            _ = subprocess.call(gams_loc+' combined_model.gms', cwd = GAMs_run_dir, shell=True)
    else:
        if stable_flags['run_seperate']:
            shutil.copyfile('../GAMs/cAct_model.gms', GAMs_run_dir+'/cAct_model.gms')
            shutil.copyfile('../GAMs/cInh_model.gms', GAMs_run_dir+'/cInh_model.gms')
            if stable_flags['supress_output']:
                _ = subprocess.call('gams cAct_model > /dev/null', shell = True, cwd = GAMs_run_dir)
                _ = subprocess.call('gams cInh_model > /dev/null', shell = True, cwd = GAMs_run_dir)
            else:
                _ = subprocess.call('gams cAct_model', shell = True, cwd = GAMs_run_dir)
                _ = subprocess.call('gams cInh_model', shell = True, cwd = GAMs_run_dir)
        elif inhibitor and not promoter:
            shutil.copyfile('../GAMs/model_inhibitor_metab_complimentary.gms', GAMs_run_dir+'/combined_model.gms')
            if stable_flags['supress_output']:
                _ = subprocess.call('gams combined_model > /dev/null', shell = True, cwd = GAMs_run_dir)
            else:
                _ = subprocess.call('gams combined_model', shell = True, cwd = GAMs_run_dir)
        elif promoter and not inhibitor:
            shutil.copyfile('../GAMs/model_activator_metab_complimentary.gms', GAMs_run_dir+'/combined_model.gms')
            if stable_flags['supress_output']:
                _ = subprocess.call('gams combined_model > /dev/null', shell = True, cwd = GAMs_run_dir)
            else:
                _ = subprocess.call('gams combined_model', shell = True, cwd = GAMs_run_dir)  
        else:
            shutil.copyfile('../GAMs/combined_model.gms', GAMs_run_dir+'/combined_model.gms')
            if stable_flags['supress_output']:
                _ = subprocess.call('gams combined_model > /dev/null', shell = True, cwd = GAMs_run_dir)
            else:
                _ = subprocess.call('gams combined_model', shell = True, cwd = GAMs_run_dir)


def run_multi_GAMs(flags_df, TF_flags_df, stable_flags, cell_constants, GAMs_run_dir, parameter_flags = None):
    ############################################################
    # save input parameters
    ############################################################
    if not parameter_flags:
        parameter_flags = stable_flags
        baby_dict = {
            'act_TF_conc_lo' : parameter_flags['act_TF_conc_lo'],
            'act_TF_conc_up' : parameter_flags['act_TF_conc_up'],
            'act_Kd_lo' : parameter_flags['act_Kd_lo'],
            'act_Kd_up' : parameter_flags['act_Kd_up'],
            'inh_TF_conc_lo' : parameter_flags['inh_TF_conc_lo'],
            'inh_TF_conc_up' : parameter_flags['inh_TF_conc_up'],
            'inh_Kd_lo' : parameter_flags['inh_Kd_lo'],
            'inh_Kd_up' : parameter_flags['inh_Kd_up'],

            'weight_act_obj1' : parameter_flags['weight_act_obj1'],
            'weight_inh_obj1' : parameter_flags['weight_inh_obj1'],
            'weight_act_obj2' : parameter_flags['weight_act_obj2'],
            'weight_inh_obj2' : parameter_flags['weight_inh_obj2'],
            'weight_mRNA_match' : parameter_flags['weight_mRNA_match'],
            'weight_act_corr' : parameter_flags['weight_act_corr'],
            'weight_inh_corr' : parameter_flags['weight_inh_corr'],
            'act_metab_Total_lo' : parameter_flags['act_metab_Total_lo'],
            'act_metab_Total_up' : parameter_flags['act_metab_Total_up'],
            'inh_metab_Total_lo' : parameter_flags['inh_metab_Total_lo'],
            'inh_metab_Total_up' : parameter_flags['inh_metab_Total_up'],
        }
    else:
        para_sweep = ['act_TF_conc_lo', 'act_TF_conc_up', 'act_Kd_lo', 'act_Kd_up', 'inh_TF_conc_lo', 'inh_TF_conc_up', 'inh_Kd_lo', 'inh_Kd_up', 'weight_act_obj1', 'weight_inh_obj1', 'weight_act_obj2', 'weight_inh_obj2', 'weight_mRNA_match', 'weight_act_corr', 'weight_inh_corr', 'inh_metab_Total_lo', 'inh_metab_Total_up', 'act_metab_Total_lo', 'act_metab_Total_up']
        baby_dict = {}
        for para in para_sweep:
            if para in parameter_flags:
                baby_dict.update({para : parameter_flags[para]})
    df = pd.DataFrame(list(baby_dict.items()), columns=['Parameter', 'Value']).set_index('Parameter')
    df.to_csv(GAMs_run_dir+'/input_files/parameters.csv')
    
    # now pull in TF specific parameters zzz need to set up proplery TODO
    baby_dict = {
        'kd_act_metab' : 0,
        'kd_inh_metab' : 0,
    }
    if True:#promoter:
        baby_dict.update({'kd_act_metab' : TF_flags_df.iloc[0].values[0]})
    if True:#inhibitor:
        baby_dict.update({'kd_inh_metab' : TF_flags_df.iloc[0].values[1]})
    df = pd.DataFrame(list(baby_dict.items()), columns=['Parameter', 'Value']).set_index('Parameter')
    df.to_csv(GAMs_run_dir+'/input_files/input_constants.csv')
    
    
    ############################################################
    # gather files needed to run GAMS
    ############################################################
    files_use = []
    for sample in stable_flags['limit_samples']:
        use_zerod_A = flags_df.loc[sample]['use_zerod_A_matrix']
        if stable_flags['use_greedy']:
            f_name = sample+'_greedy.pkl'
        else:
            f_name = sample+'.pkl'
        if os.path.exists('../data/cAct_cInh_vals/'+f_name):
            files_use.append(f_name)
                
    for f in files_use:
        shared_indices = []
        first = True
        for file in files_use:
            gene_name = file.split('.')[0].split('_')[0]
            temp_df = pd.read_pickle('../data/cAct_cInh_vals/'+file)
            if first:
                shared_indices = set(temp_df.index)
                first = False
            else:
                shared_indices = set(shared_indices.intersection(set(temp_df.index)))
        shared_indices = list(shared_indices)
        shared_indices.sort()
        act_df = pd.DataFrame(index = shared_indices)
        inh_df = pd.DataFrame(index = shared_indices)
        for file in files_use:
            gene_name = file.split('.')[0].split('_')[0]
            act_df[gene_name] = pd.read_pickle('../data/cAct_cInh_vals/'+file)['cAct'].loc[act_df.index].values
            inh_df[gene_name] = pd.read_pickle('../data/cAct_cInh_vals/'+file)['cInh'].loc[inh_df.index].values
    
    # save off max values for scaling objective functions
    vals = []
    for col in act_df.columns:
        vals.append(max(act_df[col]))
    max_df = pd.DataFrame(vals, index = act_df.columns)
    max_df.to_csv(GAMs_run_dir+'/input_files/max_cActs.csv')
    vals = []
    for col in inh_df.columns:
        vals.append(max(inh_df[col]))
    max_df = pd.DataFrame(vals, index = inh_df.columns)
    max_df.to_csv(GAMs_run_dir+'/input_files/max_cInhs.csv')
    
    # convert this into iModulon format that looks like excel so GAMS can read it
    # also need to create mapping between existing gene- iM in act and gene-iM in inh pairs
    act_gene_iM_pairs = []
    inh_gene_iM_pairs = []
    act_df = act_df.T
    inh_df = inh_df.T
    iMs = []
    keep = []
    for gene in act_df.index:
        iM = flags_df.loc[gene]['act_iM']
        if type(iM) == float:
            keep.append(False)
        else:
            act_gene_iM_pairs.append((gene, iM))
            keep.append(True)
            iMs.append(iM)
    act_df = act_df.loc[keep]
    cols = inh_df.columns.to_list()
    act_df['iM'] = iMs
    cols.insert(0, 'iM')
    act_df['iM'] = iMs
    act_df = act_df[cols]

    iMs = []
    keep = []
    for gene in inh_df.index:
        iM = flags_df.loc[gene]['inh_iM']
        if type(iM) == float:
            keep.append(False)
        else:
            inh_gene_iM_pairs.append((gene, iM))
            keep.append(True)
            iMs.append(iM)
    inh_df = inh_df.loc[keep]
    cols = inh_df.columns.to_list()
    cols.insert(0, 'iM')
    inh_df['iM'] = iMs
    inh_df = inh_df[cols]
    
    
    
    # include missing values as zeros and finish making mapping df
    all_iMs = list(set(act_df.iM).union(inh_df.iM))
    genes = list(set(act_df.index).union(set(inh_df.index)))
    needs_to_exist = [gene+';'+iM for gene, iM in itertools.product(genes, all_iMs)]
    
    # add missing to cAct
    exists = [gene+';'+iM for gene, iM in zip(act_df.index, act_df.iM)]
    to_create = list(set(needs_to_exist) - set(exists))
    new_row_indices = [val.split(';')[0] for val in to_create]
    new_iMs = [val.split(';')[1] for val in to_create]
    new_rows = pd.DataFrame(index = new_row_indices, columns = act_df.columns)
    new_rows['iM'] = new_iMs
    act_df = pd.concat([act_df, new_rows])
    act_df = act_df.fillna(0)

    # add missing to cAct
    exists = [gene+';'+iM for gene, iM in zip(inh_df.index, inh_df.iM)]
    to_create = list(set(needs_to_exist) - set(exists))
    new_row_indices = [val.split(';')[0] for val in to_create]
    new_iMs = [val.split(';')[1] for val in to_create]
    new_rows = pd.DataFrame(index = new_row_indices, columns = inh_df.columns)
    new_rows['iM'] = new_iMs
    inh_df = pd.concat([inh_df, new_rows])
    inh_df = inh_df.fillna(0)
    
    act_df.to_csv(GAMs_run_dir+'/input_files/composite_cAct_vals.csv')
    inh_df.to_csv(GAMs_run_dir+'/input_files/composite_cInh_vals.csv')
    
    # make mapping
    act_mapping_df = pd.DataFrame(index = list(set(act_df.index)), columns = all_iMs).fillna(0)
    inh_mapping_df = pd.DataFrame(index = list(set(inh_df.index)), columns = all_iMs).fillna(0)
    for gene, iM in act_gene_iM_pairs:
        act_mapping_df.at[gene, iM] = 1
    for gene, iM in inh_gene_iM_pairs:
        inh_mapping_df.at[gene, iM] = 1
    act_mapping_df.to_csv(GAMs_run_dir+'./input_files/cAct_mapping.csv')
    inh_mapping_df.to_csv(GAMs_run_dir+'./input_files/cInh_mapping.csv')
    
    # need to save off dummy dimensional dataframe
    all_samples = list(set(act_df.columns).union(inh_df.columns))
    all_samples.remove('iM')
    all_samples.insert(0, 'iM')
    new_row_indices = [val.split(';')[0] for val in needs_to_exist]
    new_iMs = [val.split(';')[1] for val in needs_to_exist]
    dummy_df = pd.DataFrame(index = new_row_indices, columns = all_samples)
    dummy_df['iM'] = new_iMs
    dummy_df = dummy_df.fillna(1)
    dummy_df.to_csv(GAMs_run_dir+'./input_files/dimensions.csv')
    
    
    ############################################################
    # save actual ratio_df values
    ############################################################
    collection = []
    index = []
    for f in files_use:
        gene_name = f.split('.')[0].split('_')[0]
        use_zerod_A = flags_df.loc[gene_name]['use_zerod_A_matrix']
        df_name = gene_name+'_zerod'+str(use_zerod_A)+'_mRNA_ratios_and_MA_vals.csv'
        ratios_df = pd.read_csv('../data/saved_mRNA_ratios_MA_vals/'+df_name, index_col = 0)
        collection.append(ratios_df['actual_mRNA_ratio'])
        index.append(gene_name)
    ratios_combo_df = pd.DataFrame(collection, index = index)
    ratios_combo_df.T.to_csv(GAMs_run_dir+'/input_files/actual_mRNA_ratio.csv')
    

    ############################################################
    # create constants files for mRNA calculation
    ############################################################
    index = []
    collection = []
    for f in files_use:
        gene_name = f.split('.')[0].split('_')[0]
        gene_grid_name = '../data/gene_grid_constants/'+gene_name+'.pkl'
        pickle_in = open(gene_grid_name, 'rb')
        grid_constants = pickle.load(pickle_in)
        pickle_in.close()
        index.append(gene_name)
        collection.append(grid_constants)
    constants_df = pd.DataFrame(collection, index = index)
    constants_df.T.to_csv(GAMs_run_dir+'/input_files/grid_constants.csv')     
    # make sample_constants file, for now just contains RNAP conc
    RNAP_conc_df = pd.read_csv('../data/RNAP_conc.csv', index_col = 0)
    RNAP_conc_df = RNAP_conc_df.loc[ratios_df.index]
    RNAP_conc_df.T.to_csv(GAMs_run_dir+'/input_files/sample_constants.csv')     
    
    
    ############################################################
    # create TF concentration
    ############################################################
    concentrations = pd.read_csv('../data/validation_data_sets/converted_log_tpm_in_M.csv', index_col = 0)
    keep = []
    old_to_new = {}
    for promoter in set(flags_df.act_iM):
        if str(promoter) == 'nan':
            continue
        gene = iM_to_b_regulator[promoter][0] # not sure how we're handling this long term, for now there shall only be one regulator of each iModulon
        keep.append(gene)
        old_to_new.update({gene : promoter})
    concentrations.loc[keep].rename(index = old_to_new).to_csv(GAMs_run_dir+'/input_files/exported_act_TF_conc.csv')
    keep = []
    old_to_new = {}
    for inhibitor in set(flags_df.inh_iM):
        if str(inhibitor) == 'nan':
            continue
        gene = iM_to_b_regulator[inhibitor][0]
        keep.append(gene)
        old_to_new.update({gene : inhibitor})
    concentrations.loc[keep].rename(index = old_to_new).to_csv(GAMs_run_dir+'/input_files/exported_inh_TF_conc.csv')
    
    
    ############################################################
    # run GAMS
    ############################################################
    # remove old results
    if stable_flags['delete_old']:
        if os.path.exists('../data/GAMS_output/cInh_Kd_results.csv'):
            os.remove('../data/GAMS_output/cInh_Kd_results.csv')
        if os.path.exists('../data/GAMS_output/cInh_TF_conc_results.csv'):
            os.remove('../data/GAMS_output/cInh_TF_conc_results.csv')
        if os.path.exists('../data/GAMS_output/cAct_Kd_results.csv'):
            os.remove('../data/GAMS_output/cAct_Kd_results.csv')
        if os.path.exists('../data/GAMS_output/cAct_TF_conc_results.csv'):
            os.remove('../data/GAMS_output/cAct_TF_conc_results.csv')

    # call GAMS
    shutil.copyfile('../GAMs/conopt.opt', GAMs_run_dir+'/conopt.opt')
    if platform.system() == 'Windows':
        gams_loc =  r'"C:\GAMS\win64\28.2\gams.exe"' # zzz shouldn't be hard set like this, but for now this is fine

        shutil.copyfile('../GAMs/merged_iMs_model.gms', GAMs_run_dir+'/combined_model.gms')
        _ = subprocess.call(gams_loc+' combined_model.gms', cwd = GAMs_run_dir, shell=True)
    else:

        shutil.copyfile('../GAMs/merged_iMs_model.gms', GAMs_run_dir+'/combined_model.gms')
        if stable_flags['supress_output']:
            _ = subprocess.call('gams combined_model > /dev/null', shell = True, cwd = GAMs_run_dir)
        else:
            _ = subprocess.call('gams combined_model', shell = True, cwd = GAMs_run_dir)


def read_GAMs(GAMs_run_dir):
    # look at GAMs results
    no_promoter = False
    no_inhibitor = False

    # load in cActivators
    saved_cActivators = pd.read_csv(GAMs_run_dir+'/input_files/composite_cAct_vals.csv', index_col = 0)
    
    # GAMS calculated cActivators
    act_kd_df = 10**pd.read_csv(GAMs_run_dir+'/output_files/cAct_Kd_results.csv', index_col = 0).astype(float).T
    
    saved_cActivators = saved_cActivators[act_kd_df.columns]
    if os.path.exists(GAMs_run_dir+'/output_files/cAct_TF_conc_results.csv'):
        cAct_kd_df = 10**pd.read_csv(GAMs_run_dir+'/output_files/cAct_Kd_results.csv', index_col = 0).astype(float).T
        saved_cActivators = saved_cActivators[cAct_kd_df.columns]
        cAct_TF_conc_df = 10**pd.read_csv(GAMs_run_dir+'/output_files/cAct_TF_conc_results.csv', index_col = 0).astype(float).T
        saved_cActivators = saved_cActivators.loc[cAct_TF_conc_df.columns]
        calc_cAct = pd.DataFrame(index = saved_cActivators.columns, columns = saved_cActivators.index)
        cActs = []
        for sample in calc_cAct.columns:
            for gene in calc_cAct.index:
                calc_cAct.at[gene, sample] = cAct_TF_conc_df[sample].values[0] / cAct_kd_df[gene].values[0]
        calc_cAct = calc_cAct.T
    else:
        # activator metabolite, no promoter model
        no_inhibitor = True
        TF_conc_df = None
        # we are using either one of the metabolite models, so need to calculate cActivator using that
        act_metab = 10**pd.read_csv(GAMs_run_dir+'/output_files/act_metab_Total.csv', index_col = 0).astype(float).T
        input_constants = pd.read_csv(GAMs_run_dir+'/input_files/input_constants.csv', index_col = 0).astype(float)
        KdArg = input_constants.loc['kd_inh_metab'].values[0]
        
        TF_concs = pd.read_csv(GAMs_run_dir+'/input_files/exported_act_TF_conc.csv', index_col = 0).astype(float)
        
        calc_cAct = pd.DataFrame(index = saved_cActivators.columns, columns = saved_cActivators.index)
        cActs = []
        for sample in calc_cAct.columns:
            ArgTotal = act_metab[sample].values[0]
            TFTotal = TF_concs.loc[sample].values[0]
            for gene in calc_cAct.index:
                KdTF = act_kd_df[gene].values[0]
                
                calc_cAct.at[gene, sample] = (3 * ArgTotal * KdTF + KdArg * KdTF +  3 * KdTF * TFTotal + \
                    ( -36 * ArgTotal * KdTF**2 * TFTotal + \
                     (3 * ArgTotal * KdTF + KdArg * KdTF + 3 * KdTF * TFTotal)**2)**.5 \
                    ) / (18 * KdTF**2)
        calc_cAct = calc_cAct.T

    # now cInhibitor
    # load in cActivators
    saved_cActivators = pd.read_csv(GAMs_run_dir+'/input_files/composite_cInh_vals.csv', index_col = 0)

    # GAMS calculated cActivators
    inh_kd_df = 10**pd.read_csv(GAMs_run_dir+'/output_files/cInh_Kd_results.csv', index_col = 0).astype(float).T

    saved_cActivators = saved_cActivators[inh_kd_df.columns]
    if os.path.exists(GAMs_run_dir+'/output_files/cInh_TF_conc_results.csv'):
        TF_conc_df = 10**pd.read_csv(GAMs_run_dir+'/output_files/cInh_TF_conc_results.csv', index_col = 0).astype(float).T
        saved_cActivators = saved_cActivators.loc[TF_conc_df.columns]
        calc_cInh = pd.DataFrame(index = saved_cActivators.columns, columns = saved_cActivators.index)
        cActs = []
        for sample in calc_cInh.columns:
            for gene in calc_cInh.index:
                calc_cInh.at[gene, sample] = TF_conc_df[sample].values[0] / inh_kd_df[gene].values[0]
        calc_cInh = calc_cInh.T
    else:
        # inhibitor metabolite, no promoter model
        no_promoter = True
        TF_conc_df = None
        # we are using either one of the metabolite models, so need to calculate cInhibitor using that
        inh_metab = 10**pd.read_csv(GAMs_run_dir+'/output_files/inh_metab_Total.csv', index_col = 0).astype(float).T
        input_constants = pd.read_csv(GAMs_run_dir+'/input_files/input_constants.csv', index_col = 0).astype(float)
        KdArg = input_constants.loc['kd_inh_metab'].values[0]
        
        TF_concs = pd.read_csv(GAMs_run_dir+'/input_files/exported_inh_TF_conc.csv', index_col = 0).astype(float)
        
        calc_cInh = pd.DataFrame(index = saved_cActivators.columns, columns = saved_cActivators.index)
        cActs = []
        for sample in calc_cInh.columns:
            ArgTotal = inh_metab[sample].values[0]
            TFTotal = TF_concs.loc[sample].values[0]
            for gene in calc_cInh.index:
                KdTF = inh_kd_df[gene].values[0]
                
                calc_cInh.at[gene, sample] = (3 * ArgTotal * KdTF + KdArg * KdTF +  3 * KdTF * TFTotal + \
                    ( -36 * ArgTotal * KdTF**2 * TFTotal + \
                     (3 * ArgTotal * KdTF + KdArg * KdTF + 3 * KdTF * TFTotal)**2)**.5 \
                    ) / (18 * KdTF**2)
        calc_cInh = calc_cInh.T
        

    # return
    if no_promoter:
        return(calc_cAct, act_kd_df, cAct_TF_conc_df, calc_cInh, inh_kd_df, inh_metab)
    elif no_inhibitor:
        return(calc_cAct, act_kd_df, act_metab, calc_cInh, inh_kd_df, TF_conc_df)
    else:
        return(calc_cAct, act_kd_df, cAct_TF_conc_df, calc_cInh, inh_kd_df, TF_conc_df)
    

def read_multi_GAMs(GAMs_run_dir):
    # look at GAMs results
    
    # inputs
    saved_cActivators = pd.read_csv(GAMs_run_dir+'/input_files/composite_cAct_vals.csv', index_col = 0)
    saved_cInhibitors = pd.read_csv(GAMs_run_dir+'/input_files/composite_cInh_vals.csv', index_col = 0)
    act_TF_concs = pd.read_csv(GAMs_run_dir+'/input_files/exported_act_TF_conc.csv', index_col = 0)
    inh_TF_concs = pd.read_csv(GAMs_run_dir+'/input_files/exported_inh_TF_conc.csv', index_col = 0)
    input_constants = pd.read_csv(GAMs_run_dir+'/input_files/input_constants.csv', index_col = 0)
    cAct_mapping = pd.read_csv(GAMs_run_dir+'/input_files/cAct_mapping.csv', index_col = 0)
    cInh_mapping = pd.read_csv(GAMs_run_dir+'/input_files/cInh_mapping.csv', index_col = 0)
    
    # outputs
    act_kd_df = pd.read_csv(GAMs_run_dir+'/output_files/cAct_Kd_results.csv', index_col = 0)
    inh_kd_df = pd.read_csv(GAMs_run_dir+'/output_files/cInh_Kd_results.csv', index_col = 0)
    act_metab = pd.read_csv(GAMs_run_dir+'/output_files/act_metab_Total.csv', index_col = 0)
    inh_metab = pd.read_csv(GAMs_run_dir+'/output_files/inh_metab_Total.csv', index_col = 0)

    # limit overlaps
    saved_cActivators = saved_cActivators.loc[act_kd_df.index]
    saved_cInhibitors = saved_cInhibitors.loc[inh_kd_df.index]

    
    # let's unlog kd_df and metab_df
    act_kd_df[act_kd_df.columns[1:]] = 10**act_kd_df[act_kd_df.columns[1:]].astype(float)
    inh_kd_df[inh_kd_df.columns[1:]] = 10**inh_kd_df[inh_kd_df.columns[1:]].astype(float)
    act_metab[act_metab.columns[1:]] = 10**act_metab[act_metab.columns[1:]].astype(float)
    inh_metab[inh_metab.columns[1:]] = 10**inh_metab[inh_metab.columns[1:]].astype(float)
    
    
    # activator calculations
    iM_to_cActs = {}
    KdArg = input_constants.loc['kd_act_metab'].values[0]
    for iM, group in act_kd_df.groupby('iM'):
        bby_kd_df = group.drop(columns = 'iM')
        bby_metab_df = act_metab[act_metab['iM'] == iM].drop(columns = 'iM')
        
        calc_cAct = pd.DataFrame(index = bby_kd_df.index, columns = bby_metab_df.index)
        for sample in calc_cAct.columns:
            
            ArgTotal = bby_metab_df.loc[sample].values[0]
            try:
                TFTotal = act_TF_concs.loc[iM][sample]
            except:
                TFTotal = 1 # generally this means there is no activator, so setting this isn't important
            for gene in calc_cAct.index:
                KdTF = bby_kd_df.loc[gene].values[0]
                if cAct_mapping.loc[gene, iM] == 0:
                    calc_cAct.at[gene, sample] = 0
                else:
                    calc_cAct.at[gene, sample] = (3 * ArgTotal * KdTF + KdArg * KdTF +  3 * KdTF * TFTotal + \
                        ( -36 * ArgTotal * KdTF**2 * TFTotal + \
                         (3 * ArgTotal * KdTF + KdArg * KdTF + 3 * KdTF * TFTotal)**2)**.5 \
                        ) / (18 * KdTF**2)
        calc_cAct = calc_cAct.T
        
        iM_to_cActs.update({iM : calc_cAct})

    
    # inhibitor calculations
    iM_to_cInhs = {}
    KdArg = input_constants.loc['kd_inh_metab'].values[0]
    for iM, group in inh_kd_df.groupby('iM'):
        bby_kd_df = group.drop(columns = 'iM')
        bby_metab_df = inh_metab[inh_metab['iM'] == iM].drop(columns = 'iM')
        
        
        
        calc_cInh = pd.DataFrame(index = bby_kd_df.index, columns = bby_metab_df.index)
        for sample in calc_cInh.columns:
            ArgTotal = bby_metab_df.loc[sample].values[0]
            TFTotal = inh_TF_concs.loc[iM][sample]
            for gene in calc_cInh.index:
                KdTF = bby_kd_df.loc[gene].values[0]
                if cInh_mapping.loc[gene, iM] == 0:
                    calc_cInh.at[gene, sample] = 0
                else:
                    calc_cInh.at[gene, sample] = (3 * ArgTotal * KdTF + KdArg * KdTF +  3 * KdTF * TFTotal + \
                        ( -36 * ArgTotal * KdTF**2 * TFTotal + \
                         (3 * ArgTotal * KdTF + KdArg * KdTF + 3 * KdTF * TFTotal)**2)**.5 \
                        ) / (18 * KdTF**2)
        calc_cInh = calc_cInh.T
        
        iM_to_cInhs.update({iM : calc_cInh})  
     
    # return
    return(iM_to_cActs, act_kd_df, act_metab, iM_to_cInhs, inh_kd_df, inh_metab)
    