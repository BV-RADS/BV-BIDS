import os
import sys
import argparse
import glob

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="This script counts the number of MRI runs matching a specific string in a BIDS dataset. "
                    "It outputs a TSV file with the counts for each subject and session.",
        epilog="Example usage: python RunCount_query.py -bd /path/to/BIDS -st axial_T1"
    )
    parser.add_argument('-bd', '--bidsdir', required=True, help="Path to the BIDS directory")
    parser.add_argument('-st', '--strings', required=True, help="String to search in filenames (e.g., 'axial_T1')")
    return parser.parse_args()

def count_runs(bidsdir, search_string):
    count_data = []
    for subject in os.listdir(bidsdir):
        subject_dir = os.path.join(bidsdir, subject)
        if os.path.isdir(subject_dir) and subject.startswith("sub-"):
            for session in os.listdir(subject_dir):
                session_dir = os.path.join(subject_dir, session)
                if os.path.isdir(session_dir) and session.startswith("ses-"):
                    files = glob.glob(f"{session_dir}/**/*{search_string}*.nii*", recursive=True)
                    count_data.append([subject, session, len(files)])
    return count_data

def write_to_tsv(data, output_file):
    with open(output_file, 'w') as file:
        file.write("Subject\tSession\tFileCount\n")
        for row in data:
            file.write("\t".join(map(str, row)) + "\n")

def main():
    args = parse_arguments()
    counts = count_runs(args.bidsdir, args.strings)
    output_filename = f"RunCount_{args.strings}.tsv"
    write_to_tsv(counts, output_filename)
    print(f"Output written to {output_filename}")

if __name__ == "__main__":
    main()

