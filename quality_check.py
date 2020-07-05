import os
import pandas as pd
import argparse
import sys
import re
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('-ws_1', action='store', required=True, help='Path to worksheet 1 output files include TSHC_<ws>_version dir')
parser.add_argument('-ws_2', action='store', help='Path to worksheet 2 output files include TSHC_<ws>_version dir')
parser.add_argument('-out_dir', action='store', help='Specifing an output directory to store html reports')
parser.add_argument('-samplesheet', action='store', help='SampleSheet requrired for HO panel quality checks')
args = parser.parse_args()



def get_inputs(ws_1, ws_2):
    '''
    All TSHC runs are conducted in pairs. The get_inputs function defines the
    following variables for a paired set of outputs:
        2) xls_rep_2- excel report (1st w/s in pair) 
        3) neg_rep- excel report for negative samples (1 per pair)
        4) fastq_bam_1 - fastq-bam comparison excel report (1st w/s in pair) 
        5) fastq_bam_2 - fastq-bam comparison excel report (2nd w/s in pair) 
        6) kin_xls - kinship report for pair
        7) vcf_dir_1 - path to vcf output directory (1st w/s in pair)
        8) vcf_dir_2  - path to vcf output directory (2nd w/s in pair)
        9) cmd_log_1 - command run text file (1st w/s in pair)
        10) cmd_log_2 - command run text file (2nd w/s pair)
        11) Panel - Name of panel

    TODO- Moving panel assignment out of this function.

    '''

    ws_1_run_info = re.search(r'\/(\w{4,7})_(\d{6})_(v[\.]?\d\.\d\.\d)\/', ws_1)    
    ws_2_run_info = re.search(r'\/(\w{4,7})_(\d{6})_(v[\.]?\d\.\d\.\d)\/', ws_2)  

    if ws_1_run_info == None or ws_2_run_info == None:
        raise Exception('Run information not available! Check regex pattern.')

    ws_1_panel = ws_1_run_info.group(1)
    ws_1_name = ws_1_run_info.group(2)
    ws_1_version = ws_1_run_info.group(3)
    ws_2_panel = ws_2_run_info.group(1)
    ws_2_name = ws_2_run_info.group(2)
    ws_2_version = ws_2_run_info.group(3)
    
    if ws_1_panel == ws_2_panel:
        panel = ws_1_panel
    else:
        raise Exception('Panels from ws_1 and ws_2 do not match!')

    # defining excel inputs
    ws_1_excel_reports = ws_1 + 'excel_reports_{}_{}/'.format(ws_1_panel, ws_1_name)
    ws_1_list = pd.DataFrame(os.listdir(ws_1_excel_reports), columns=['sample_name'])
    ws_2_excel_reports = ws_2 + 'excel_reports_{}_{}/'.format(ws_2_panel, ws_2_name)
    ws_2_list = pd.DataFrame(os.listdir(ws_2_excel_reports), columns=['sample_name'])

    xls_rep_1 = ws_1_list[~ws_1_list['sample_name'].str.contains('Neg|-fastq-bam-check|merged-variants')]
    xls_rep_2 = ws_2_list[~ws_2_list['sample_name'].str.contains('Neg|-fastq-bam-check|merged-variants')]
    neg_rep_1 = ws_1_list[ws_1_list['sample_name'].str.contains('Neg')]
    neg_rep_2 = ws_2_list[ws_2_list['sample_name'].str.contains('Neg')]
    fastq_xls_1 = ws_1_list[ws_1_list['sample_name'].str.contains('fastq-bam-check')]
    fastq_xls_2 = ws_2_list[ws_2_list['sample_name'].str.contains('fastq-bam-check')]

    xls_rep_1 = ws_1_excel_reports + xls_rep_1.values[0][0]
    xls_rep_2 = ws_2_excel_reports + xls_rep_2.values[0][0]

    #determine which ws contains the negative sample
    if len(neg_rep_1) != 0:
        neg_rep = ws_1_excel_reports + neg_rep_1.values[0][0]
    elif len(neg_rep_2) != 0:
        neg_rep = ws_2_excel_reports + neg_rep_2.values[0][0]
    else:
        raise Exception('Error the negative sample is not present!')

    # get fastq-bam-check file names 
    fastq_bam_1 = ws_1_excel_reports + fastq_xls_1.values[0][0]
    fastq_bam_2 = ws_2_excel_reports + fastq_xls_2.values[0][0]

    # defining vcf directory path 
    vcf_dir_1 = ws_1 + 'vcfs_{}_{}/'.format(ws_1_panel, ws_1_name)
    vcf_dir_2 = ws_2 + 'vcfs_{}_{}/'.format(ws_2_panel, ws_2_name)

    # defining cmd_log and kin
    cmd_log_1 = ws_1 + '{}.commandline_usage_logfile'.format(ws_1_name)
    cmd_log_2 = ws_2 + '{}.commandline_usage_logfile'.format(ws_2_name)
    kin_xls = ws_1 + '{}_{}.king.xlsx'.format(ws_1_name, ws_2_name)
    

    return xls_rep_1, xls_rep_2, neg_rep, fastq_bam_1, fastq_bam_2, kin_xls, vcf_dir_1, vcf_dir_2, cmd_log_1, cmd_log_2, panel



def results_excel_check(res, check_result_df):
    '''
    2 independent checks are completed on each excel report generated by the pipeline:
        a) 20x coverage check- Column V of the 'Hyb-QC' tab. PASS if all samples >96% (excludes D00-00000)
        b) VerifyBamId check- Coulmn I of the 'VerifyBamId' tab. PASS if all samples <3% 
    A description of the checks and a PASS/FAIL result for a given check are then added to the check_result_df
    '''

    xls = pd.ExcelFile(res)
    hybqc_df = pd.read_excel(xls, 'Hyb-QC')
    verify_bam_id_df = pd.read_excel(xls, 'VerifyBamId')
    
    work_num = os.path.basename(res)
    worksheet_name = re.search(r'\d{6}', work_num)[0]
    
    # list of all % coverage at 20x (excluding control) 
    coverage_list = hybqc_df[~hybqc_df['Sample'].str.contains('D00-00000')]['PCT_TARGET_BASES_20X'].values
    coverage_check = '20x coverage check'
    coverage_check_des = 'A check to determine if 96% of all target bases in each sample are covered at >=20X'
    coverage_result = 'PASS'

    for value in coverage_list:
        if value < 0.96:
            coverage_result = 'FAIL'
            
    #list all VerifyBamId results (inc control)
    verify_bam_list = verify_bam_id_df['%CONT'].values
    verify_bam_check = 'VerifyBamId check'
    verify_bam_check_des = 'A check to determine if all samples in a worksheet have contamination <3%'
    verify_bam_result = 'PASS'
    for value in verify_bam_list:
        if value >= 3:
            verify_bam_result = 'FAIL'
    
    check_result_df = check_result_df.append({'Check': verify_bam_check,
                            'Description': verify_bam_check_des,
                            'Result': verify_bam_result, 'Worksheet': worksheet_name}, ignore_index=True)
    
    check_result_df = check_result_df.append({'Check': coverage_check,
                            'Description': coverage_check_des,
                            'Result': coverage_result, 'Worksheet':worksheet_name}, ignore_index=True)
    
    return check_result_df
    
    
def neg_excel_check(neg_xls, check_result_df):
    '''
    2 independent checks on the negative sample excel report produced by the pipeline run (1 per pair):
        a) Numer of exons- In the 'Coverage-exon' tab 1204 exons should be present
        b) Max number of reads in negative- In column M of the 'Coverage-exon' no max should be > 0

    A description of the checks and a PASS/FAIL result for a given check are then added to the check_result_df
    '''
    
    work_num = os.path.basename(neg_xls)
    worksheet_name = re.search(r'\d{6}', work_num)[0]
    
    xls = pd.ExcelFile(neg_xls)
    neg_exon_df = pd.read_excel(xls, 'Coverage-exon')

    # number of exons check
    num_exons_check = 'Number of exons in negative sample'
    num_exons_check_des = 'A check to determine if 1207 exons are present in the negative control (Coverage-exon tab)'
    
    if len(neg_exon_df) == 1207:
        num_exons_check_result = 'PASS'
    else:
        num_exons_check_result = 'FAIL'
    
    cov_neg_exons_check = 'Contamination of negative sample'
    cov_neg_exons_check_des = 'A check to determine if the max read depth of the negative sample is equal to 0'
    max_neg_coverage = neg_exon_df['Max'].values

    over_1x = []
    for depth in set(max_neg_coverage):
        if depth >= 1:
            over_1x.append(depth)

    if len(over_1x) >= 1:
        cov_neg_exons_check_result = 'FAIL'
    else:
        cov_neg_exons_check_result = 'PASS'


    check_result_df = check_result_df.append({'Check': num_exons_check,
                                                'Description': num_exons_check_des,
                                                'Result': num_exons_check_result,
                                                'Worksheet': worksheet_name}, ignore_index=True)

    check_result_df = check_result_df.append({'Check': cov_neg_exons_check,
                                                'Description': cov_neg_exons_check_des,
                                                'Result': cov_neg_exons_check_result,
                                                'Worksheet': worksheet_name}, ignore_index=True)
    
    return check_result_df



def kinship_check(kin_xls, check_result_df):
    '''
    A check to determine if any sample the kinship.xls file has a kinship values of >=0.48
    A description of the check and a PASS/FAIL result for the check is then added to the check_result_df
    '''
    worksheet_name = re.search(r'\/(\d{6}_\d{6}).king.xlsx.*', kin_xls).group(1)

    kinship_check = 'Kinship check'
    kinship_check_des = 'A check to ensure that all samples in a worksheet pair have a kinship value of <0.48'
    
    xls = pd.ExcelFile(kin_xls)
    kinship_df = pd.read_excel(xls, 'Kinship')
    
    kinship_values = kinship_df['Kinship'].values
    
    if max(kinship_values) >= 0.48:
        kinship_check_result = 'FAIL'
    else:
        kinship_check_result = 'PASS'
    
    # Additional step to set fail for any kinship result containing inf and nan values 
    for kin in kinship_values:
        if np.isnan(kin) == True or np.isinf(kin) == True:
            kinship_check_result = 'FAIL'
    
    check_result_df = check_result_df.append({'Check': kinship_check,
                                                'Description': kinship_check_des,
                                                'Result': kinship_check_result,
                                                'Worksheet': worksheet_name}, ignore_index=True)
    
    return check_result_df



def vcf_dir_check(vcf_dir, check_result_df):
    '''
    A check to see if 48 VCF files have been generated
    A description of the check and a PASS/FAIL result for the check is then added to the check_result_df
    '''

    worksheet_name = str(re.search(r'\/vcfs_\w{4}_(\d{6})\/', vcf_dir).group(1))
    vcf_dir_check = 'VCF file count check'
    vcf_dir_check_des = 'A check to determine if 48 VCFs have been generated'
    
    if len(os.listdir(vcf_dir)) == 48:
        vcf_dir_check_result = 'PASS'
    else:
        vcf_dir_check_result = 'FAIL'
    
    check_result_df = check_result_df.append({'Check': vcf_dir_check,
                                                'Description': vcf_dir_check_des,
                                                'Result': vcf_dir_check_result,
                                                'Worksheet': worksheet_name}, ignore_index=True)
    
    return check_result_df


def fastq_bam_check(fastq_xls, check_result_df):
    '''
    A check to determine that the expected number of reads are present in each FASTQ and BAM file
    A description of the check and a PASS/FAIL result for the check is then added to the check_result_df
    '''
    
    work_num = os.path.basename(fastq_xls)
    worksheet_name = re.search(r'\d{6}', work_num)[0]
    

    fastq_bam_check = 'FASTQ-BAM check'
    fastq_bam_check_des = 'A check to determine that the expected number of reads are present in each FASTQ and BAM file'
    xls = pd.ExcelFile(fastq_xls)
    fastq_bam_df = pd.read_excel(xls, 'Check')
    fastq_bam = set(fastq_bam_df['Result'].values)

    if 'FAIL' in fastq_bam:
        fastq_bam_check_result = 'FAIL'
    else:
        fastq_bam_check_result = 'PASS'
    
    check_result_df = check_result_df.append({'Check': fastq_bam_check,
                                                'Description': fastq_bam_check_des,
                                                'Result': fastq_bam_check_result,
                                                'Worksheet': worksheet_name}, ignore_index=True)

    return check_result_df

def generate_html_output(check_result_df, run_details_df, panel, bed_1, bed_2):
    '''
    Creating a static HTML file to display the results to the Clinical Scientist reviewing the quality check report.
    This function calls the format_bed_files function to add in bed file information.
    This process involves changes directly to the html. TODO find replacement method to edit html.
    '''

    with open('css_style.css') as file:
        style = file.read()
    run_details = run_details_df.to_html(index=False, justify='left')
    run_details = format_bed_files(run_details, bed_1, bed_2)
    check_details = check_result_df.to_html(index=False, justify='left')

    report_head = f'<h1>{panel} Quality Report</h1>'
    run_sub = '<h2>Run details<h2/>'
    check_sub = '<h2>Checks<h2/>'
    html = f'<!DOCTYPE html><html><head>{style}</head><body>{report_head}{run_sub}{run_details}{check_sub}{check_details}</body></hml>'

    # Add class to PASS/FAIL to colour code
    html = re.sub(r"<td>PASS</td>",r"<td class='PASS'>PASS</td>", html)
    html = re.sub(r"<td>FAIL</td>",r"<td class='FAIL'>FAIL</td>", html)

    file_name = "_".join(run_details_df['Worksheet'].values.tolist()) + '_quality_checks.html'

    return file_name, html


def format_bed_files(run_html, bed_1, bed_2):
    '''
    Adding the bed file html table to the run html table. The bed file information is passed as 
    a list for each worksheet in the pair. [ws_1_html, search_term]. The html contains bed file
    information for the worksheet e.g. target bed, refined bed and coverage bed... This is then
    substituted into the html by searching for the ws search term e.g. 000001_bed_files.
    '''

    bed_1_html = bed_1[0]
    bed_1_search = bed_1[1]
    bed_2_html = bed_2[0]
    bed_2_search = bed_2[1]
    run_html = re.sub(f'{bed_1_search}', f'{bed_1_html}', run_html)
    run_html = re.sub(f'{bed_2_search}', f'{bed_2_html}', run_html)

    # rename dataframe bed_table to bed_table... css classes cannot have spaces
    run_html = re.sub('<td><table border="1" class="dataframe bed_table">', '<td><table border="1" class="bed_table">', run_html)

    return run_html

def run_details(cmd,xls_rep,run_details_df):
    '''
    Collect the following run details from the commandline_usage_logfile and excel report
        1) CMD log file- Worksheet number and experiment name
        2) excel report- Worksheet number, AB threshold, pipeline version and BED files
    Add run details to run details_df
    '''
    bed_files = []
    bed_df = pd.DataFrame(columns=['Target bed', 'Refined bed', 'Coverage bed'])

    # get ws names for the cmd file and
    cmd_ws = re.search(r'(\d{6})\.commandline_usage_logfile', cmd)
    xls_ws = re.search(r'(\d{6})-\d{2}-D\d{2}-\d{5}-\w{2,3}-\w+-\d{3}_S\d+\.v\d\.\d\.\d-results\.xlsx', xls_rep)

    if cmd_ws == None:
        raise Exception('Input error- issue with commandline_usage_logfile')
    elif xls_ws == None:
        raise Exception('Input error- xls input worksheet not present.')

    cmd_ws = cmd_ws.group(1)
    xls_ws = xls_ws.group(1)

    # check that the cmd and xls report are from the same worksheet
    if cmd_ws != xls_ws:
        raise Exception('The worksheet numbers: {} and {} do not match!'.format(cmd_ws, xls_ws))

    worksheet = cmd_ws

    # get experiment name from command output
    with open(cmd, 'r') as file:
        cmd_text = file.read()
    search_term = r'-s\s\n\/network\/sequenced\/MiSeq_data\/\w{4,7}\/(shire_worksheet_numbered|Validation)\/(?:200000-299999\/)?(?:300000-399999\/)?' + re.escape(worksheet) + r'\/(\d{6}_M\d{5}_\d{4}_\d{9}-\w{5})\/SampleSheet.csv'

    experiment_name = re.search(search_term, cmd_text).group(2)
    
    if experiment_name == None:
        raise Exception('The experiment name is not present! check regex pattern.')

    # get pipeline version, bed file names and AB threshold
    xls = pd.ExcelFile(xls_rep)
    config_df = pd.read_excel(xls, 'config_parameters')
    allele_balance = config_df[config_df['key']=='AB_threshold']['variable'].values[0]
    pipe_version = config_df[config_df['key']=='pipeline version']['variable'].values[0]
    target_bed = config_df[config_df['key']=='target_regions']['variable'].values[0].split('/')[-1]
    refined_target_bed = config_df[config_df['key']=='refined_target_regions']['variable'].values[0].split('/')[-1]
    coverage_bed = config_df[config_df['key']=='coverage_regions']['variable'].values[0].split('/')[-1]

    bed_file_table = f'{worksheet}_bed_files'

    bed_df = bed_df.append({
        'Target bed': target_bed,
        'Refined bed': refined_target_bed,
        'Coverage bed': coverage_bed
        }, ignore_index=True)

    bed_df = bed_df.transpose()
    bed_html = bed_df.to_html(justify='left', header=None, escape=True, classes='bed_table', border=0)

    bed = [bed_html, bed_file_table]

    run_details_df = run_details_df.append({'Worksheet': worksheet,
                                            'Pipeline version': pipe_version,
                                            'Experiment name': experiment_name,
                                            'Bed files': bed_file_table,
                                            'AB threshold': allele_balance
                                            }, ignore_index=True)

    return run_details_df, bed

def tshc_main(ws_1, ws_2):
    '''
    A function to organise the TSHC output quality check function calls

    '''

    xls_rep_1, xls_rep_2, neg_rep, fastq_bam_1, fastq_bam_2, kin_xls, vcf_dir_1, vcf_dir_2, cmd_log_1, cmd_log_2, panel = get_inputs(ws_1, ws_2)

    pd.set_option('display.max_colwidth', -1)
    check_result_df = pd.DataFrame(columns=[ 'Worksheet','Check', 'Description','Result'])
    run_details_df = pd.DataFrame(columns=['Worksheet', 'Pipeline version', 'Experiment name', 'Bed files', 'AB threshold'])

    # ws_1 checks
    check_result_df = results_excel_check(xls_rep_1, check_result_df)
    check_result_df = vcf_dir_check(vcf_dir_1, check_result_df)
    check_result_df = fastq_bam_check(fastq_bam_1, check_result_df)

    # ws_2 checks
    check_result_df = results_excel_check(xls_rep_2, check_result_df)
    check_result_df = vcf_dir_check(vcf_dir_2, check_result_df)
    check_result_df = fastq_bam_check(fastq_bam_2, check_result_df)

    # pair checks
    check_result_df = neg_excel_check(neg_rep, check_result_df)
    check_result_df = kinship_check(kin_xls, check_result_df)

    # run details
    run_details_df, bed_1 = run_details(cmd_log_1, xls_rep_1, run_details_df)
    run_details_df, bed_2 = run_details(cmd_log_2, xls_rep_2, run_details_df)

    # sort
    check_result_df = check_result_df.sort_values(by=['Worksheet'])
    run_details_df = run_details_df.sort_values(by=['Worksheet'])
    #create static html output
    name, html_report = generate_html_output(check_result_df,run_details_df, panel, bed_1, bed_2)

    # write html report to both results directories
    ws_1_out = args.ws_1
    ws_2_out = args.ws_2

    if args.out_dir == None:
        os.chdir(ws_1_out)
        with open(name, 'w') as file:
            file.write(html_report)
        os.chdir(ws_2_out)
        with open(name, 'w') as file:
            file.write(html_report)
    else:
        print(f'Saving html reports to {args.out_dir}')
        os.chdir(args.out_dir)
        with open(name, 'w') as file:
            file.write(html_report)

def assign_panel(ws_1, ws_2, sample_sheet):
    '''
    Assiging a panel and <panel>_main funtion to process pipeline output.
    
    TODO --> For now I have implemented this for TSMP... other panels to follow

    '''
    panel = re.search(panel_regex, ws_1).group(1)

    if panel == 'TSMP':
        tsmp_main(ws_1, sample_sheet)
    elif panel == 'TSHC':
        tshc_main(ws_1, ws_2)
    else:
        print('Are you sure....Never heard of this panel')


def tsmp_main(ws_1, sample_sheet):
    '''
    A function to organise the TSMP function calls

    The following functions must be run to produce the quality check report:

    1. Assign varaiables for samples in worksheet (sort_tsmp_inputs)

    2. get_run details table 
    '''

    result_files = sort_tsmp_inputs(ws_1)
    sample_1 = result_files['samples'][0]
    sample_1_xls = pd.ExcelFile(sample_1)
    hybqc = pd.read_excel(sample_1_xls, 'Hyb-QC')

    thirty_only = hybqc['PCT_TARGET_BASES_30X']
    all_cov = hybqc[['PCT_TARGET_BASES_20X', 'PCT_TARGET_BASES_30X', 'PCT_TARGET_BASES_40X']]

    print(all_cov)


def sort_tsmp_inputs(ws_1):
    '''
    a function to a dictionary of inputs: neg_ws_result, all_result_paths,
    vcf_path, 

    {
    worksheet_num: {
    negative: '/path/to/neg',
    samples: ['/path/to/sample_1', '/path/to/samp_2'....], 
    cmd_log_file: 'path_to_log'
    vcf_directory: '/path/to/vcfs',
    sry_excel: '/path/to/sry'
    }}
    
    for the majority of checks use sample_1 one, for FLT3 check use whole list

    TODO: write this function!
    '''

    tsmp_inp =     {
    'negative': '/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/000001-1-D00-00000-NEG_S1.v0.5.3-results.xlsx',
    'samples': ['/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/000001-2-D20-00001-JD_S2.v0.5.3-results.xlsx'], 
    'cmd_log_file': '/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/000001.commandline_usage_logfile',
    'vcf_directory': '/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/vcfs_TSMP_000001',
    'sry_excel': '/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/000001-SRY.xlsx',
    'merged_variant_xls':'/home/degan/mock_ngs_out/mock_input_data/TSMP/TSMP_000001_v0.5.3/excel_reports_TSMP_000001/TSMP_000001.merged-variants.xlsx'
    }
    
    return tsmp_inp

# Generic regex used to extact ws_num etc
# TODO replace TSHC section with variable name
panel_regex = r'\/(\w{4,7})_(\d{6})_(v[\.]?\d\.\d\.\d)\/'

ws_1 = args.ws_1
ws_2 = args.ws_2
sample_sheet = args.samplesheet

# Assign panel and start workflow
assign_panel(ws_1, ws_2, sample_sheet)


#tshc_main(ws_1, ws_2)