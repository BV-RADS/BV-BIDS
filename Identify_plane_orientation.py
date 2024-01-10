#!/usr/bin/env python3
"""
Identify Plane Orientation Script

This script processes MRI image files in a BIDS dataset to identify their plane orientations 
(axial, coronal, sagittal, or oblique). It can process all subjects within the BIDS directory
or specific subjects. The script also handles renaming of files to include the identified plane 
orientation in their filename and processes 'run-' patterns in filenames.

Usage:
    python script_name.py --bidsdir <path_to_bidsdir> [--all | --subjects <subject_ids>] [--strings <strings>]

Arguments:
    --bidsdir : Path to the BIDS dataset directory.
    --all     : Process all subjects in the BIDS directory.
    --subjects: Process specific subjects. List subject IDs separated by spaces.
    --strings : List of strings to search for in file names. Defaults to ['_T1'].

Examples:
    python script_name.py --bidsdir /path/to/bidsdir --all
    python script_name.py --bidsdir /path/to/bidsdir --subjects sub-01 sub-02
    python script_name.py --bidsdir /path/to/bidsdir --all --strings _T1 _T2

"""

import os
import sys
import argparse
import glob
import json
import shutil

def determine_plane(orientation):
    x_vec, y_vec = orientation[:3], orientation[3:]
    x_dominant = x_vec.index(max(x_vec, key=abs))
    y_dominant = y_vec.index(max(y_vec, key=abs))

    if x_dominant == y_dominant:
        return "oblique"
    elif x_dominant == 1 and y_dominant == 2:
        return "sagittal"
    elif x_dominant == 0 and y_dominant == 2:
        return "coronal"
    elif x_dominant == 0 and y_dominant == 1:
        return "axial"
    else:
        return "oblique"

def process_file_for_plane(target_folder, file):
    print(f"Processing file for plane determination: {file}")
    if any(plane in file for plane in ["axial", "coronal", "sagittal", "oblique"]):
        print(f"File {file} already contains plane information. Skipping.")
        return

    json_path = os.path.join(target_folder, file)
    with open(json_path, 'r') as f:
        data = json.load(f)

    orientation = data.get("ImageOrientationPatientDICOM", None)
    if orientation and len(orientation) == 6:
        plane = determine_plane(orientation)
        rename_file_based_on_plane(target_folder, file, plane, json_path)
    else:
        print(f"Orientation data not found or incomplete in {file}")


def rename_file_based_on_plane(target_folder, file, plane, json_path):
    print(f"Determined plane: {plane} for file: {file}")
    parts = file.split('_')
    if len(parts) > 2:
        parts.insert(2, f'acq-{plane}')
        new_filename = '_'.join(parts)
        new_json_path = os.path.join(target_folder, new_filename)
        rename_files(json_path, new_json_path)
    else:
        print(f"Filename format not as expected: {file}")

def rename_files(old_path, new_path):
    if os.path.exists(new_path):
        print(f"Warning: File {new_path} already exists. Skipping rename.")
        return

    print(f"Renaming {old_path} to {new_path}")
    shutil.move(old_path, new_path)

    old_nii_path = old_path.replace('.json', '.nii.gz')
    new_nii_path = new_path.replace('.json', '.nii.gz')
    if os.path.exists(old_nii_path):
        rename_files(old_nii_path, new_nii_path)

def process_subjects(bidsdir, subjects, strings):
    for subject in subjects:
        subject_path = os.path.join(bidsdir, subject)
        if os.path.isdir(subject_path):
            for session in os.listdir(subject_path):
                session_path = os.path.join(subject_path, session)
                if os.path.isdir(session_path):
                    # Iterate through all subdirectories in the session path
                    for subdir in os.listdir(session_path):
                        subdir_path = os.path.join(session_path, subdir)
                        if os.path.isdir(subdir_path):
                            # Process files for plane determination
                            for file in os.listdir(subdir_path):
                                if file.endswith('.json') and any(s in file for s in strings):
                                    process_file_for_plane(subdir_path, file)
                            
                            # Process files to handle 'run-' pattern
                            process_files_for_run(subdir_path)


def process_files_for_run(target_folder):
    print(f"Processing files for 'run-' pattern in {target_folder}")
    files = [f for f in os.listdir(target_folder) if f.endswith('.json')]
    potential_new_names = {}

    for file in files:
        if 'run-' in file:
            new_name = '_'.join(part for part in file.split('_') if not part.startswith('run-'))
            potential_new_names.setdefault(new_name, []).append(file)

    for new_name, file_group in potential_new_names.items():
        if len(file_group) == 1:
            old_file = file_group[0]
            old_json_path = os.path.join(target_folder, old_file)
            new_json_path = os.path.join(target_folder, new_name)
            rename_files(old_json_path, new_json_path)
        else:
            print(f"Skipping rename for {file_group} as it would result in duplicate filenames.")

def rename_files_in_directory(target_folder, strings):
    print(f"Processing directory: {target_folder}")
    if not os.path.exists(target_folder):
        print(f"Error: Directory {target_folder} does not exist.")
        return

    # Process files for plane determination
    for file in os.listdir(target_folder):
        if file.endswith('.json') and any(s in file for s in strings):
            process_file_for_plane(target_folder, file)

    # Process files to handle 'run-' pattern
    process_files_for_run(target_folder)



def parse_arguments():
    parser_description = __doc__  # This takes the module's docstring
    parser = argparse.ArgumentParser(description=parser_description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--bidsdir', type=str, required=True, help='Path to BIDS directory')
    parser.add_argument('--all', action='store_true', help='Process all subjects')
    parser.add_argument('--subjects', nargs='+', help='List of subject IDs to process')
    parser.add_argument('--strings', nargs='+', default=['_T1'], help='List of strings to search for in file names (default: ["_T1"])')
    return parser.parse_args()


def main():
    args = parse_arguments()
    bidsdir = args.bidsdir

    if not os.path.exists(bidsdir):
        print(f"Error: BIDS directory {bidsdir} does not exist.")
        sys.exit(1)

    if args.all:
        subjects = [d for d in os.listdir(bidsdir) if os.path.isdir(os.path.join(bidsdir, d)) and d.startswith('sub-')]
    elif args.subjects:
        subjects = args.subjects
    else:
        print("Error: Please specify subjects to process or use the --all flag.")
        sys.exit(1)

    process_subjects(bidsdir, subjects, args.strings)

if __name__ == "__main__":
    main()








if __name__ == "__main__":
    main()

