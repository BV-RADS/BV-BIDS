#!/usr/bin/env python3
import os
import subprocess
import sys
import pydicom
import shutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def anonymize_dicom_file(input_file, output_file, patient_id):
    try:
        ds = pydicom.dcmread(input_file, force=True)

        # Define tags to anonymize
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
        print(f"Anonymized files in {os.path.relpath(root, input_dir)}")

def main():
    bidsfolder = os.path.dirname(os.path.realpath(__file__))

    # Set the current working directory to the location of this script
    os.chdir(bidsfolder)

    # Query for subject and session
    subject = input("Enter subject ID (e.g., sub-001): ")
    session = input("Enter session ID (e.g., ses-01): ")

    # Create BIDS directory structure
    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")
    print("Creating BIDS directory structure.")
    scaffold_cmd = ["dcm2bids_scaffold", "-o", bidsdir_folder]
    subprocess.run(scaffold_cmd)

    anon_dicom_folder = os.path.join(bidsfolder, ".temp_anondir")
    raw_dicom_folder = os.path.join(bidsfolder, "Inbox")
    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")
    
    # Check if the subject/session directory already exists
    target_dir = os.path.join(bidsfolder, "BIDSDIR", subject, session)
    if os.path.isdir(target_dir):
        print(f"The directory {target_dir} already exists. Please review this conflict.")
        sys.exit(1)

    anon_sorted_dicom_folder = os.path.join(bidsfolder, "BIDSDIR", "sourcedata", subject)
    dcm2bids_config = "dcm2bids_config.json"
   

    print("Preparing directories for anonymization.")
    os.makedirs(anon_dicom_folder, exist_ok=True)
    os.makedirs(anon_sorted_dicom_folder, exist_ok=True)

    # Process directories
    print("Processing directories for anonymization.")
    process_directory(raw_dicom_folder, anon_dicom_folder, subject)

    # Sort and convert DICOM files
    print("Sorting and converting DICOM files.")
    dicom_sort_cmd = ["dicom_sort", "--copy", anon_dicom_folder, anon_sorted_dicom_folder, "%StudyDate%/%SeriesDescription%"]
    subprocess.run(dicom_sort_cmd)

    # Run dcm2bids
    print("Running dcm2bids for NIfTI conversion.")
    dcm2bids_cmd = ["dcm2bids", "-d", raw_dicom_folder, "-p", subject, "-s", session, "-c", dcm2bids_config, "-o", bidsdir_folder]
    subprocess.run(dcm2bids_cmd)

    # Clean up
    print("Cleaning up temporary files.")
    shutil.rmtree(anon_dicom_folder)

    print("Process completed.")

if __name__ == "__main__":
    main()

