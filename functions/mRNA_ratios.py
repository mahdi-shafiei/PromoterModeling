import pandas as pd
import numpy as np



def calculate_mRNA_ratios_and_MA_values(iM_act, iM_inh, input_parameters):
    # unload flags
    gene = input_parameters['central_gene']
    use_zerod_A_matrix = input_parameters['use_zerod_A_matrix']
    basal_conditions = input_parameters['basal_conditions']
    
    
    # loading
    M_df = pd.read_csv('../data/precise_1.0/M.csv', index_col = 0)
    iM_table = pd.read_csv('../data/precise_1.0/iM_table.csv', index_col = 0)
    M_df = M_df.rename(columns = {str(index) : row['name'] for index, row in iM_table.iterrows()})
    log_tpm_df = pd.read_csv('../data/precise_1.0/log_tpm.csv', index_col = 0)
    
    # creates zerod matrices
    if use_zerod_A_matrix:
        gene_iMs_df = pd.read_csv('../data/precise_1.0/gene_presence_matrix.csv', index_col = 0)
        gene_iMs_df.columns = M_df.columns
        genes_to_zero = list(gene_iMs_df.index[[val for val in gene_iMs_df[[iM_act, iM_inh]].T.any()]])
        iMs_to_zero = list(set(gene_iMs_df.columns) - set([iM_act, iM_inh]))

        zerod_M = M_df.copy()
        zerod_M.loc[genes_to_zero, iMs_to_zero] = 0
        #zerod_M = zerod_M.drop(columns = ['fps__fps_ptsI_ale3__1', 'fps__fps_ptsI_ale3__2', 'fps__fps_ptsI_ale1__1', 'fps__fps_ptsI_ale1__2'])

        # Calculate the inverse of DataFrame M
        M_inverse = pd.DataFrame(np.linalg.pinv(zerod_M.values), zerod_M.columns, zerod_M.index)

        # Solve for DataFrame A: A = M_inverse * X
        #fixed_X = log_tpm_df.div(log_tpm_df[basal_conditions].mean(axis = 1), axis = 'index')
        fixed_X = log_tpm_df.sub(log_tpm_df[basal_conditions].mean(axis = 1), axis = 'index')
        fixed_X = fixed_X.fillna(0).drop(columns = ['fps__fps_ptsI_ale3__1', 'fps__fps_ptsI_ale3__2', 'fps__fps_ptsI_ale1__1', 'fps__fps_ptsI_ale1__2'])
        zerod_A_df = M_inverse.dot(fixed_X)

        A_df = zerod_A_df
        M_df = zerod_M



    # create data matrix
    act_MAs = []
    inh_MAs = []
    index = []
    actual_counts = []
    log_x_c = log_tpm_df.loc[gene][basal_conditions].mean()
    # predict mRNA values
    for key, val in (A_df.loc[iM_act].T*(M_df[iM_act].loc[gene])).items():
        index.append(key)
        act_MAs.append(val)
        actual_counts.append(2**(log_tpm_df.loc[gene][key]) / 2**(log_x_c))
    for key, val in (A_df.loc[iM_inh].T*(M_df[iM_inh].loc[gene])).items():
        inh_MAs.append(val)

    values_df = pd.DataFrame(index = index)
    values_df['MA_activator'] = act_MAs
    values_df['MA_inhibitor'] = inh_MAs
    values_df['actual_mRNA_ratio'] = actual_counts


    
    return(values_df)