# BV-RADS BIDS dataset creation toolkit

The BV-RADS BIDS Dataset Creation Toolkit our custom solution for integrating multi-site and heterogeneous study samples into imaging research within the Brain Imaging Data Structure (BIDS) format. It streamlines three key processes:

1. *BV-BIDS Add_study:* Converts DICOM to NIfTI, anonymizes DICOM files, and organizes data into BIDS format, ensuring compliance and data privacy.

2. *Plane Identification Tool:* Identifies and labels the plane orientation of MRI images, particularly useful for multi-plane clinical MR imaging atasets.

3. *BIDS Viewer Script:* Facilitates quick visualization of MRI sequences, allowing for easy inspection across different subjects.

4. *RunCount Script:* Counts the number of runs that match a specified string. Quick detection of repeated or absent runs accross subjects and sessions.

This toolkit enhances the workflow from DICOM processing to BIDS-compliant data organization and visualization, providing a seamless experience for researchers handling complex neuroimaging datasets.

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

## 1. BV-BIDS Add_study

This pipeline is designed to streamline the integration of new patient data into the Brain Imaging Data Structure (BIDS) format. It not only converts DICOM files to NIfTI for BIDS compliance but also anonymizes the DICOM files and organizes them in the `sourcedata` folder. A key feature of this toolkit is its capability to save both the BIDS-compatible files and the anonymized DICOM files, addressing the frequent need for access to the original DICOM data in research settings.

This tool merely streamlines the use of:
- [pydicom](https://pydicom.github.io/) for dicom anonymization
- [simple-dicom-sort](https://pypi.org/project/simple-dicom-sort/) for sorting the dicoms
- [dcm2niix](https://github.com/rordenlab/dcm2niix) and [dcm2bids](https://unfmontreal.github.io/Dcm2Bids/3.1.1/) for nifti conversion and BIDS sorting.
 		


### Usage

### Preparation
1. **Prepare Your DICOM Files**: Place your unsorted DICOM files in the `inbox` folder with any folder and naming structure.

2. **Configuration**: A project-specific the `dcm2bids_config.json` file must  be defined only once per project. An example config file is provided, but it must be tailored to your project, modify as needed. Refer to the following resources: 
- [How to create a config file in the dcm2bids documentation](https://unfmontreal.github.io/Dcm2Bids/3.1.1/how-to/create-config-file/) 
- [BIDS "get started" website](https://bids.neuroimaging.io/get_started.html)

### Processing
 **Option 1. Single subject processing**: 
For single subject script it is not necessary to fill in the `ID_correspondence.tsv`. Instead, just run: 
```bash
python AddStudy.py
```
   - Follow the prompts to enter the subject ID (e.g., `sub-001`) and session ID (e.g., `ses-01`) and the script will anonymize and sort dicoms, then convert to .nii.gz and organize in a bids system .

 **Option 2: Multiple subjects batch processing**: 
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

 **Manual Cleanup**:
Remember to manually delete the files in the inbox folder after processing is complete.


### WARNING!
While NIFTI files are simpler to anonymize. DICOM headers are very heterogeneous among vendors. We have designed the anonymization method to comply with anonymization for our sample and vendor. However, we cannot guarantee that private tags in other dicom studies, especially from other vendors will be completely anonymized. We therefore urge the users to thoroughly review the resulting dicom headers prior to data sharing. 

Furthermore, the anonymization process may sometimes undesiredly alter crucial dicom tags, especially in multi-volume files such as DTI, BOLD, or perfusion. We highly recommend veryfing the validity of the resulting files and preservation of the original dicom files. 

## 2. Plane Identification Tool
### Overview
The `Identify_plane_orientation.py` script is specifically tailored for clinical 2D thick slab MR imaging where multiple planes (axial, coronal, sagittal, oblique) are often acquired. This tool is particularly useful in scenarios where different planes are converted by dcm2bids as distinct runs, which might be challenging to filter using the dcm2bids configuration file.

This tool is particularly advantageous for datasets with clinical MRI scans, where plane identification directly influences the dataset's structure and usability in research. It ensures that each image's plane orientation is clearly identified, aiding researchers in efficiently sorting and utilizing the dataset.

### Functionality
- Processes MRI image files in any subdirectory within each subject's folder in a BIDS dataset.
- Identifies the plane orientation of the images and renames files to include this information, aiding in the organization and identification of images.
- Handles filenames with 'run-' patterns, renaming them for consistency and avoiding duplicates.
- Offers flexibility to specify custom strings for searching within file names.
- Especially useful for datasets with clinical 2D images, where plane identification is crucial for accurate data interpretation and sorting.

### Usage
1. *Run the Script:*
- To process all subjects:
```bash
python Identify_plane_orientation.py --bidsdir /path/to/bidsdir --all
```
- To process specific subjects:
```bash
python Identify_plane_orientation.py --bidsdir /path/to/bidsdir --subjects sub-01 sub-02
```
- To use custom strings for file search:
```bash
python Identify_plane_orientation.py --bidsdir /path/to/bidsdir --all --strings _T1 _T2
```

2. *View the output:*
- The script will process the specified subjects or all subjects in the BIDS directory.
- Renamed files will reflect the identified plane orientation directly in their filenames.


## 3. BIDS Viewer Script
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
```bash
python bids_viewer.py /path/to/BIDSDIR t1w t2w flair t1c
```

2. If the sequence name strings are not provided as arguments, the script will prompt you to enter them.

3. View the Output: After the script completes, it generates an output.html file in the same directory. Open this file in a web browser to view the table of MRI slices.


## RunCount Query Script
### Overview
The `RunCount_query.py` script counts the number of runs that match a specified string within a BIDS dataset. This tool can be to quickly assess repeated runs or absent scans of specific  MRI sequences or scans across different subjects and sessions.

### Functionality
- The script searches for .nii or .nii.gz files in a BIDS directory that contain the specified string in their filenames.
- It works recursively, ensuring that all files within the session directories are accounted for.
- The output is a TSV (Tab Separated Values) file that lists each subject and session, along with the count of files matching the specified string.

### Usage
1. *Run the Script:* Execute the script with the path to the BIDS directory and the string you want to search for. For example
```python
python RunCount_query.py -bd /path/to/BIDS -st axial_T1
```

2. *View the Results:* The script outputs a TSV file named RunCount_<search_string>.tsv, e.g., `RunCount_axial_T1.tsv`. This file will be in the directory where the script was run. Open the TSV file with any text editor or spreadsheet program to view the results.

