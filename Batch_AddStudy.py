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
import argparse
import glob

"""
DICOM Processing Script

This script processes DICOM files for medical imaging research. It supports anonymization,
sorting, conversion to BIDS format, and populating participant data. Various steps in the process can be skipped using 
command line flags.

Usage:
    python script_name.py [options]

Options:
    --noanon          Skip the anonymization step.
    --nosort          Skip the sorting step.
    --nobids          Skip the conversion to BIDS format.
    --nocleanup       Skip cleanup of temporary unsorted anonymized dicom dir.
    --noparticipants  Skip populating participants.tsv file.
"""



def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Processes DICOM files for medical imaging research.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--noanon', 
        action='store_true', 
        help='Skip the anonymization step (use if data is already anonymized).'
    )
    parser.add_argument(
        '--nosort', 
        action='store_true', 
        help='Skip the sorting step (use if sorting is not required).'
    )
    parser.add_argument(
        '--nobids', 
        action='store_true', 
        help='Skip the conversion to BIDS format (use if conversion is already done or not needed).'
    )

    parser.add_argument(
        '--nocleanup', 
        action='store_true', 
        help='Skip cleanup of temporary unsorted anonymized dicom dir.'
    )

    parser.add_argument(
        '--noparticipants',
        action='store_true',
        help='Skip populating participants.tsv file.'
    )
    return parser.parse_args()


def read_subject_mapping(filename):
    df = pd.read_csv(filename, sep=r'\s+', header=None, dtype=str)
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



def populate_participants_tsv(inbox_folder, participant_map_file, bidsdir_folder):
    participant_map = read_subject_mapping(participant_map_file)
    participants_file = os.path.join(bidsdir_folder, "participants.tsv")

    required_columns = ["participant_id", "age", "sex", "notes"]
    should_append = file_has_required_columns(participants_file, required_columns)

    if not should_append:
        with open(participants_file, "w") as file:
            file.write("participant_id\tage\tsex\tgroup\tnotes\toriginal_id\n")

    participants_data = {}  # Initialize the participants_data dictionary

    with open(participants_file, "a" if should_append else "w") as file:
        if not should_append:
            file.write("participant_id\tage\tsex\tgroup\tnotes\toriginal_id\n")

        for root, dirs, files in os.walk(inbox_folder):
            for file_name in files:
                if is_dicom_file(file_name):
                    dicom_file = os.path.join(root, file_name)
                    ds = pydicom.dcmread(dicom_file)
                    original_patient_id = ds.PatientID if 'PatientID' in ds else "Unknown"
                    age = ds.PatientAge if 'PatientAge' in ds else ""
                    sex = ds.PatientSex if 'PatientSex' in ds else ""
                    new_patient_id = participant_map.get(original_patient_id, "Unknown")
                    if new_patient_id not in participants_data:
                        participants_data[new_patient_id] = [new_patient_id, age, sex, "", "", original_patient_id]
                    break  # Break after processing the first DICOM file in each folder

        for data in participants_data.values():
            file.write("\t".join(data) + "\n")

def file_has_required_columns(file_path, required_columns):
    """Check if a file has the required columns."""
    try:
        df = pd.read_csv(file_path, sep='\t')
        return all(column in df.columns for column in required_columns)
    except Exception:
        return False
        

def main():
    args = parse_arguments()
    bidsfolder = os.path.dirname(os.path.realpath(__file__))
    os.chdir(bidsfolder)

    

    # Read subject mapping
    subject_map = read_subject_mapping("ID_correspondence.tsv")
    patient_id_map = subject_map

    # Directory setup
    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")
    sourcedata_dir = os.path.join(bidsdir_folder, "sourcedata")
    raw_dicom_folder = os.path.join(bidsfolder, "Inbox")
    anon_dicom_folder = os.path.join(bidsfolder, ".temp_anondir")
    dcm2bids_config = "dcm2bids_config.json"

    # BIDS directory setup
    if not os.path.exists(bidsdir_folder):
        print("Creating BIDS directory structure.")
        scaffold_cmd = ["dcm2bids_scaffold", "-o", bidsdir_folder]
        subprocess.run(scaffold_cmd)
    else:
        print(f"BIDS directory structure already exists at {bidsdir_folder}.")

    os.makedirs(sourcedata_dir, exist_ok=True)
    os.makedirs(anon_dicom_folder, exist_ok=True)



    # Run participants_data.py script
    if not args.noparticipants:
        print("Populating participants.tsv file.")
        populate_participants_tsv(os.path.join(bidsfolder, "Inbox"), 
                                  "ID_correspondence.tsv", 
                                  os.path.join(bidsfolder, "BIDSDIR"))



    # Anonymization step
    if not args.noanon:
        process_directory(raw_dicom_folder, anon_dicom_folder, patient_id_map)
    
    if not args.nosort:
        print("Sorting DICOM files.")
        from dicom_sorting_tool import sort_dicom
        sort_dicom(anon_dicom_folder, sourcedata_dir)


    # dcm2bids step
    if not args.nobids:
        process_new_sessions(sourcedata_dir, bidsdir_folder, dcm2bids_config)

    if not args.nocleanup:
        shutil.rmtree(anon_dicom_folder)

    print("Batch process completed.")



if __name__ == "__main__":
    main()

