# Bellvitge Radiomics dicom/nifti BIDS sorting tool

This pipeline is designed to streamline the integration of new patient data into the Brain Imaging Data Structure (BIDS) format. It not only converts DICOM files to NIfTI for BIDS compliance but also anonymizes the DICOM files and organizes them in the `sourcedata` folder. A key feature of this toolkit is its capability to save both the BIDS-compatible files and the anonymized DICOM files, addressing the frequent need for access to the original DICOM data in research settings.

This tool merely streamlines the use of:
- pydicom for dicom anonymization
- simple-dicom-sort for sorting the dicoms
- dcm2niix/dcm2bids for nifti conversion and BIDS sorting.
 		

## Important Note
The anonymization process may occasionally alter critical DICOM tags due to the complex and sensitive nature of the DICOM format. It is strongly recommended that users maintain a legally accessible, original version of the DICOM files without anonymization, as a precaution and for future reference.

## Installation

### Setting Up the Conda Environment

1. **Clone the Repository**:
```bash
git clone [repository URL]
```

2. **Install Conda**: Download and install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

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
- [`How to create a config file` in the dcm2bids documentation](https://unfmontreal.github.io/Dcm2Bids/3.1.1/how-to/create-config-file/) 
- [BIDS "get started" website](https://bids.neuroimaging.io/get_started.html)

3. **Run the Processing Script**
```bash
python AddStudy.py
```
   - Follow the prompts to enter the subject ID (e.g., `sub-001`) and session ID (e.g., `ses-01`) and the script will anonymize and sort dicoms, then convert to .nii.gz and organize in a bids system .

4. **Manual Cleanup**: Remember to manually delete the files in the inbox folder after processing is complete.
