# Automated HO and TSHC Quality Checks

This script automates the manual quality checks completed by Clinical Scientists within the Haemato-Oncology (HO) and Familial Cancer (FC) teams. The script processes pipeline output from the MiSeq Universal pipeline (TSHC, CLL and TSMP panels) and summaries QC information in an HTML report. This report will then be reviewed by a Clinical Scientist within the HO or FC team and any fails recorded in the report will be investigated by the reviewer.

## TSHC checks

Table 1- Checks completed by the quality_check.py script for paired TSHC worksheets.
 
|\#  | Worksheet | Check                              | Description                                                                                   |
|----|-----------|------------------------------------|-----------------------------------------------------------------------------------------------|
| 1  | ws_1      | VerifyBamId check                  | A check to determine if all samples in a worksheet have contamination <3%                    |
| 2  | ws_1      | 20X coverage check                 | A check to determine if 96% of all target bases in each sample are covered at >=20X  |
| 3  | ws_1      | VCF file count check               | A check to determine if 48 VCFs have been generated                                           |
| 4  | ws_1      | FASTQ-BAM check                    | A check to determine that the expected number of reads are present in each FASTQ and BAM file |
| 5  | neg_excel | Number of exons in negative sample | A check to determine if 1350 exons are present in the negative control (Coverage-exon tab)    |
| 6  | neg_excel | Contamination of negative sample   | A check to determine if the max read depth of the negative sample is equal to 0               |
| 7  | ws_1 & ws_2      | Kinship check                      | A check to ensure that all samples in a worksheet pair have a kinship value of <0.48|
| 8  | ws_2      | VerifyBamId check                  | A check to determine if all samples in a worksheet have contamination <3%                    |
| 9  | ws_2      | 20X coverage check                 | A check to determine if 96% of all target bases in each sample are covered at >=20X  |
| 10 | ws_2      | VCF file count check               | A check to determine if 48 VCFs have been generated                                           |
| 11 | ws_2      | FASTQ-BAM check                    | A check to determine that the expected number of reads are present in each FASTQ and BAM file |

## TSMP checks

Table 2- Checks completed by the quality_check.py script for a single TSMP worksheet.

|\#  | Worksheet | Check                              | Description                                                                                   |
|----|-----------|------------------------------------|-----------------------------------------------------------------------------------------------|
| 1  | ws_1      | VCF count check                  |   The number of VCFs produced must be 2 times the number of samples present on the samplesheet.                |
| 2  | ws_1      | 	Negative exon check                 |There are 491 exons present in the negative sample.  |
| 3  | ws_1      | Negative exon depth check               | The maximum depth of each exon of the negative sample does not exceed 30 reads.                                           |
| 4  | ws_1      | Negative calls check                    | There are no calls in the negative control. |
| 5  | ws_1 | VerifyBamId check | Percentage contamination is below 10%.    |
| 6  | ws_1 | SRY check   | SRY Excel spreadsheet has been produced.               |
| 7  | ws_1      | FLT3 ITD check                      | FLT3 ITD variants are present on the FLT3 tab for samples on this worksheet.   |
| 8  | ws_1      | Gene 200x check                 | All samples in this worksheet have genes at >80% 200x.                   |
| 9  | ws_1      | Exon 100x check                 | All samples in this worksheet have exon coverage at 100x. |

In addition to the above checks being assigned a PASS or FAIL status, the report will also present additional information such as the minimum and maximum VCF file sizes, negative exon information for samples > 30 reads and the number of alt reads and singletons present in the negative sample.

## CLL checks

Table 3- Checks completed by the quality_check.py script for a single CLL worksheet.

|\#  | Worksheet | Check                              | Description                                                                                   |
|----|-----------|------------------------------------|-----------------------------------------------------------------------------------------------|
| 1  | ws_1      | VCF count check                  |   The number of VCFs produced must be 2 times the number of samples present on the samplesheet.                |
| 2  | ws_1      | 	Negative exon check                 |There are 150 exons present in the negative sample.  |
| 3  | ws_1      | Negative exon depth check               | The maximum depth of each exon of the negative sample does not exceed 30 reads.                                           |
| 4  | ws_1      | Negative calls check                    | There are no calls in the negative control. |
| 5  | ws_1 | VerifyBamId check | Percentage contamination is below 10%.    |
| 6  | ws_1 | SRY check   | SRY Excel spreadsheet has been produced.               |
| 7  | ws_1      | FLT3 ITD check                      | FLT3 ITD variants are present on the FLT3 tab for samples on this worksheet.   |
| 8  | ws_1      | Gene 300x check                 | All samples in this worksheet have genes at >80% 200x.                   |
| 9  | ws_1      | Exon 100x check                 | All samples in this worksheet have exon coverage at 100x. |

In addition to the above checks being assigned a PASS or FAIL status, the report will also present additional information such as min and max VCF size, negative exon information of samples > 30 reads and number of alt reads and singletons present in the negative sample.

## Running the quality check script

### TSHC example:

```
$ source /path/to/qc_venv/bin/activate

$ cd /path/to/ngs_quality_check/

$ python quality_check.py -ws_1 /path/to/000001/TSHC_000001_v1.0.3/ -ws_2 /path/to/000002/TSHC_000002_v1.0.3/

```
### TSMP and CLL example

```
$ source /path/to/qc_venv/bin/activate

$ cd /path/to/ngs_quality_check/

$ python quality_check.py -ws_1 /path/to/000001/<TSMP/CLL>_000001_v1.0.3/ -s /path/to/SampleSheet.csv

```

Full arguments:

| Argument    | Description                                                      |
|-------------|------------------------------------------------------------------|
| ws_1 	      | Path to the 1st TSHC output folder/ TSMP or CLL output folder					     |
| ws_2        | Path to the 2nd TSHC output folder/ Not required for TSMP or CLL worksheets							     |
| out_dir     | Optional- Path to a folder to store the HTML report output from the script. If no out_dir is specified the HTML report will be saved in each of the TSHC/TSMP/CLL output folder/s.|

