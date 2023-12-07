#!/usr/bin/env python3
import os
import subprocess
import sys
import pydicom
import shutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import pandas as pd
from datetime import datetime, timedelta
import glob

def read_subject_mapping(filename):
    df = pd.read_csv(filename, sep='\s+', header=None, dtype=str)
    # Map DICOM PatientID to new subject ID (e.g., '41411412222222': 'sub-001')
    return {row[1]: 'sub-' + row[0].zfill(3) for _, row in df.iterrows()}


def anonymize_dicom_file(input_file, output_file, patient_id_map):
    try:
        ds = pydicom.dcmread(input_file, force=True)
        patient_id = ds.get((0x0010, 0x0020))

        if patient_id and patient_id.value in patient_id_map:
            new_patient_id = patient_id_map[patient_id.value]

            tags_to_anonymize = {
                (0x0010, 0x0010): new_patient_id,  # Patient's Name
                (0x0010, 0x0020): new_patient_id,  # Patient ID
                (0x0010, 0x0030): "20000101",      # Patient's Birth Date
                "InstitutionName": "NONE",
                "DeviceSerialNumber": "NONE",
                "StationName": "NONE"
            }

            for tag, value in tags_to_anonymize.items():
                if tag in ds:
                    ds[tag].value = value

            ds.save_as(output_file)
        else:
            print(f"Patient ID {patient_id.value} not found in ID_correspondence.tsv. Skipping {input_file}")

    except Exception as e:
        print(f"Error processing {input_file}: {e}")

def anonymize_wrapper(args):
    src_file, dest_file, patient_id_map = args
    shutil.copy(src_file, dest_file)
    anonymize_dicom_file(dest_file, dest_file, patient_id_map)

def is_dicom_file(filename):
    """Check if a file is likely to be a DICOM file."""
    return filename.lower().endswith('.dcm') or '.' not in filename

def process_directory(input_dir, output_dir, patient_id_map):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    num_cores = multiprocessing.cpu_count()
    max_threads = max(1, num_cores - 2)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        tasks = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, input_dir)
                dest_file = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                args = (src_file, dest_file, patient_id_map)
                tasks.append(executor.submit(anonymize_wrapper, args))

        for future in tasks:
            future.result()


def get_new_session_number(subject_dir):
    existing_sessions = glob.glob(os.path.join(subject_dir, 'ses-*'))
    if existing_sessions:
        last_session_num = max([int(os.path.basename(s).split('-')[1]) for s in existing_sessions])
        return f'ses-{str(last_session_num + 1).zfill(2)}'
    else:
        return 'ses-01'

def process_new_sessions(sourcedata_dir, bidsdir_folder, dcm2bids_config):
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    for subject in os.listdir(sourcedata_dir):
        subject_dir = os.path.join(sourcedata_dir, subject)
        if os.path.isdir(subject_dir):
            for studydate in os.listdir(subject_dir):
                studydate_path = os.path.join(subject_dir, studydate)
                
                # Get the modification time of the folder
                folder_mod_time = datetime.fromtimestamp(os.path.getmtime(studydate_path))

                if folder_mod_time > one_hour_ago:
                    session = get_new_session_number(os.path.join(bidsdir_folder, subject))
                    dcm2bids_cmd = [
                        "dcm2bids", "-d", studydate_path, "-p", subject, 
                        "-s", session, "-c", dcm2bids_config, "-o", bidsdir_folder
                    ]
                    print("Executing:", ' '.join(dcm2bids_cmd))  # Print the command for verification
                    result = subprocess.run(dcm2bids_cmd, capture_output=True, text=True)
                    print(result.stdout)  # Print standard output
                    print(result.stderr, file=sys.stderr)  # Print standard error to stderr




def main():
    bidsfolder = os.path.dirname(os.path.realpath(__file__))
    os.chdir(bidsfolder)

    subject_map = read_subject_mapping("ID_correspondence.tsv")

    patient_id_map = subject_map


    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")
    sourcedata_dir = os.path.join(bidsdir_folder, "sourcedata")
    raw_dicom_folder = os.path.join(bidsfolder, "Inbox")
    anon_dicom_folder = os.path.join(bidsfolder, ".temp_anondir")
    dcm2bids_config = "dcm2bids_config.json"

    if not os.path.exists(bidsdir_folder):
        print("Creating BIDS directory structure.")
        scaffold_cmd = ["dcm2bids_scaffold", "-o", bidsdir_folder]
        subprocess.run(scaffold_cmd)
    else:
        print(f"BIDS directory structure already exists at {bidsdir_folder}.")

    os.makedirs(sourcedata_dir, exist_ok=True)
    os.makedirs(anon_dicom_folder, exist_ok=True)

    process_directory(raw_dicom_folder, anon_dicom_folder, patient_id_map)


    print("Sorting DICOM files.")
    dicom_sort_cmd = ["dicom_sort", "--copy", anon_dicom_folder, sourcedata_dir, "%PatientID%/%StudyDate%/%SeriesDescription%"]
    subprocess.run(dicom_sort_cmd)

    process_new_sessions(sourcedata_dir, bidsdir_folder, dcm2bids_config)
 
    shutil.rmtree(anon_dicom_folder)
    print("Batch process completed.")

if __name__ == "__main__":
    main()

