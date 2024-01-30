#!/usr/bin/env python3
import os
import subprocess
import sys
import pydicom
import shutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import argparse
import pandas as pd
from dicom_sorting_tool import sort_dicom


"""
DICOM Processing Script

This script processes individual DICOM files for medical imaging research. It supports anonymization,
sorting, and conversion to BIDS format. The script prompts for subject and session IDs instead of reading from a TSV file.

Usage:
    python AddStudy.py

The script will prompt for the subject ID and session ID.
"""

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Processes individual DICOM files for medical imaging research.",
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




def anonymize_dicom_file(input_file, output_file, patient_id):
    try:
        ds = pydicom.dcmread(input_file, force=True)
        tags_to_anonymize = {
            (0x0010, 0x0010): patient_id,  # Patient's Name
            (0x0010, 0x0020): patient_id,  # Patient ID
            (0x0010, 0x0030): "20000101",  # Patient's Birth Date
            "InstitutionName": "NONE",
            "DeviceSerialNumber": "NONE",
            "StationName": "NONE"
        }

        for tag, value in tags_to_anonymize.items():
            if tag in ds:
                ds[tag].value = value

        ds.save_as(output_file)
    except Exception as e:
        print(f"Error processing {input_file}: {e}")

def anonymize_wrapper(args):
    src_file, dest_file, patient_id = args
    shutil.copy(src_file, dest_file)
    anonymize_dicom_file(dest_file, dest_file, patient_id)

def process_directory(input_dir, output_dir, patient_id):
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
                args = (src_file, dest_file, patient_id)
                tasks.append(executor.submit(anonymize_wrapper, args))

        for future in tasks:
            future.result()



def file_has_required_columns(file_path, required_columns):
    """Check if a file has the required columns."""
    try:
        df = pd.read_csv(file_path, sep='\t')
        return all(column in df.columns for column in required_columns)
    except Exception:
        return False

def populate_participants_tsv(bidsdir_folder, subject, patient_id):
    participants_file = os.path.join(bidsdir_folder, "participants.tsv")
    required_columns = ["participant_id", "age", "sex", "group", "notes"]

    should_append = file_has_required_columns(participants_file, required_columns)
    with open(participants_file, "a" if should_append else "w") as file:
        if not should_append:
            file.write("participant_id\tage\tsex\tgroup\tnotes\n")
        # Replace with actual age, sex, group, and notes data as applicable
        file.write(f"{subject}\tage\tsex\tgroup\tnotes\n")




def main():
    args = parse_arguments()

    bidsfolder = os.path.dirname(os.path.realpath(__file__))
    os.chdir(bidsfolder)

    subject = input("Enter subject ID (e.g., sub-001): ")
    session = input("Enter session ID (e.g., ses-01): ")

    # Directory setup
    sourcedata_dir = os.path.join(bidsfolder, "BIDSDIR", "sourcedata")
    raw_dicom_folder = os.path.join(bidsfolder, "Inbox")
    anon_dicom_folder = os.path.join(bidsfolder, ".temp_anondir")
    dcm2bids_config = os.path.join(bidsfolder,"dcm2bids_config.json")
    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")  # Correct output directory for dcm2bids

    if not os.path.exists(sourcedata_dir):
        os.makedirs(sourcedata_dir)

    if not args.noanon:
        print("Processing directories for anonymization.")
        process_directory(raw_dicom_folder, anon_dicom_folder, subject)


    if not args.nosort:
        print("Sorting DICOM files.")
        sort_dicom(anon_dicom_folder, sourcedata_dir)


    if not args.nobids:
        print("Running dcm2bids for NIfTI conversion.")
        dcm2bids_cmd = ["dcm2bids", "-d", anon_dicom_folder, "-p", subject, "-s", session, "-c", dcm2bids_config, "-o", bidsdir_folder]
        subprocess.run(dcm2bids_cmd)

    if not args.nocleanup:
        shutil.rmtree(anon_dicom_folder)

    # Populate participants.tsv
    if not args.noparticipants:
        print("Populating participants.tsv file.")
        populate_participants_tsv(os.path.join(bidsfolder, "BIDSDIR"), subject, subject)

    print("Process completed.")


if __name__ == "__main__":
    main()

