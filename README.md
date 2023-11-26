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
git clone https://github.com/navalpablo/BV-BIDS-Create
```

2. **Install Conda**: 
Download and install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

3. **Create Conda Environment**:
```bash
conda env create -f environment.yml
```

4. **Activate the Environment**:
```bash
conda activate bellvitge_bids
```

### Usage

1. **Prepare Your DICOM Files**: Place your unsorted DICOM files in the `inbox` folder with any folder and naming structure.

2. Configuration: A project-specific the `BIDSDIR/code/dcm2bids_config.json` file must  be defined only once per project. An example config file is provided, but it must be tailored to your project, modify as needed. Refer to the following resources: 
- [How to create a config file in the dcm2bids documentation](https://unfmontreal.github.io/Dcm2Bids/3.1.1/how-to/create-config-file/) 
- [BIDS "get started" website](https://bids.neuroimaging.io/get_started.html)

3. **Run the Processing Script**
```bash
python AddStudy.py
```
   - Follow the prompts to enter the subject ID (e.g., `sub-001`) and session ID (e.g., `ses-01`) and the script will anonymize and sort dicoms, then convert to .nii.gz and organize in a bids system .

4. **Manual Cleanup**: Remember to manually delete the files in the inbox folder after processing is complete.


### WARNING!
While NIFTI files are simpler to anonymize. DICOM headers are very heterogeneous among vendors. We have designed the anonymization method to comply with anonymization for our sample and vendor. However, we cannot guarantee that private tags in other dicom studies, especially from other vendors will be completely anonymized. We therefore urge the users to thoroughly review the resulting dicom headers prior to data sharing. 

Furthermore, the anonymization process may sometimes undesiredly alter crucial dicom tags, especially in multi-volume files such as DTI, BOLD, or perfusion. We highly recommend veryfing the validity of the resulting files and preservation of the original dicom files. 


