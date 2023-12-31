# BV-RADS dicom/nifti BIDS sorting tool

This pipeline is designed to streamline the integration of new patient data into the Brain Imaging Data Structure (BIDS) format. It not only converts DICOM files to NIfTI for BIDS compliance but also anonymizes the DICOM files and organizes them in the `sourcedata` folder. A key feature of this toolkit is its capability to save both the BIDS-compatible files and the anonymized DICOM files, addressing the frequent need for access to the original DICOM data in research settings.

This tool merely streamlines the use of:
- [pydicom](https://pydicom.github.io/) for dicom anonymization
- [simple-dicom-sort](https://pypi.org/project/simple-dicom-sort/) for sorting the dicoms
- [dcm2niix](https://github.com/rordenlab/dcm2niix) and [dcm2bids](https://unfmontreal.github.io/Dcm2Bids/3.1.1/) for nifti conversion and BIDS sorting.
 		

## Installation

### Setting Up the Conda Environment

1. **Clone the Repository**:
```bash
git clone https://github.com/BV-RADS/BV-BIDS
```

2. **Install Conda**: 
Download and install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

3. **Create Conda Environment**:
```bash
conda env create -f environment.yml
```

4. **Activate the Environment**:
```bash
conda activate BV-RADS
```

## Usage

## Preparation
1. **Prepare Your DICOM Files**: Place your unsorted DICOM files in the `inbox` folder with any folder and naming structure.

2. **Configuration**: A project-specific the `dcm2bids_config.json` file must  be defined only once per project. An example config file is provided, but it must be tailored to your project, modify as needed. Refer to the following resources: 
- [How to create a config file in the dcm2bids documentation](https://unfmontreal.github.io/Dcm2Bids/3.1.1/how-to/create-config-file/) 
- [BIDS "get started" website](https://bids.neuroimaging.io/get_started.html)

## Processing
### **Option 1. Single subject processing**: 
For single subject script it is not necessary to fill in the `ID_correspondence.tsv`. Instead, just run: 
```bash
python AddStudy.py
```
   - Follow the prompts to enter the subject ID (e.g., `sub-001`) and session ID (e.g., `ses-01`) and the script will anonymize and sort dicoms, then convert to .nii.gz and organize in a bids system .

### **Option 2: Multiple subjects batch processing**: 
To process multiple subjects, use the  `Batch_AddStudy.py` script. Before running, fill in the `ID_correspondence.tsv` file with the two columns

- First column: First column: New PatientID (e.g., 'sub-001')
- Second column: Old PatientID corresponding to the Dicom tag to be anonymized

Run the script:

```bash
python Batch_AddStudy.py
```

The script processes subjects based on `ID_correspondence.tsv`, automatically assigning new session numbers. Ensure to process sessions consecutively.

First column: New PatientID (e.g., 'sub-001')
Second column: Old PatientID to be anonymized
Run the script:

### **Manual Cleanup**:
Remember to manually delete the files in the inbox folder after processing is complete.


### WARNING!
While NIFTI files are simpler to anonymize. DICOM headers are very heterogeneous among vendors. We have designed the anonymization method to comply with anonymization for our sample and vendor. However, we cannot guarantee that private tags in other dicom studies, especially from other vendors will be completely anonymized. We therefore urge the users to thoroughly review the resulting dicom headers prior to data sharing. 

Furthermore, the anonymization process may sometimes undesiredly alter crucial dicom tags, especially in multi-volume files such as DTI, BOLD, or perfusion. We highly recommend veryfing the validity of the resulting files and preservation of the original dicom files. 



## BIDS Viewer Script
### Overview
The `bids_viewer.py` script is a valuable addition to the BV-RADS toolkit, designed to enhance the visualization of MRI sequences in BIDS-formatted datasets. It simplifies the process of quickly inspecting specific MRI sequences across different subjects.

### Functionality
- The script processes NIfTI files (.nii or .nii.gz) located in the BIDS-formatted dataset.
- Users can specify one or more strings (e.g. t1w, t2w, etc.) that will be searched for in the image file basenames.
- For each identified image, the script extracts the middle axial slice from each subject's data and displays it in an HTML file.
- The resulting HTML file contains a table where each row represents a different subject and each column corresponds to one of the entered sequences.
- If multiple files match a sequence for a subject, the script marks this as "MULTI" in the table. If no matching files are found for a sequence in a subject's directory, it shows "NONE."

### Usage
1. Run the Script: Execute the script with the path to the BIDS directory. Optionally, you can also provide the sequence name strings directly as arguments. For example:
```python
python bids_viewer.py /path/to/BIDSDIR t1w t2w flair t1c
```

2. If the sequence name strings are not provided as arguments, the script will prompt you to enter them.

3. View the Output: After the script completes, it generates an output.html file in the same directory. Open this file in a web browser to view the table of MRI slices.
