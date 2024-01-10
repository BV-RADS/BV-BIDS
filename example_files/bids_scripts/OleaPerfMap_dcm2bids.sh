
#!/bin/bash

# Usage function to display help for the script
usage() {
    echo "Usage: $0 --bidsdir BIDSDIR --ID_table ID_TABLE --input INPUT_DIR"
    echo "  --bidsdir -bd   Path to the BIDSDIR directory"
    echo "  --ID_table -id  Path to the ID correspondence file"
    echo "  --input -in     Path to the directory containing DICOM files"
    echo "  --session -se   Session number to be applied to ALL converted studies. Introduce ful folder names (so for ses-01 introduce 'ses-01', not just '01'"
    exit 1
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -bd|--bidsdir) bidsdir="$2"; shift ;;
        -id|--ID_table) ID_table="$2"; shift ;;
        -in|--input) input="$2"; shift ;;
        -se|--session) session="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Check if all arguments are provided
if [ -z "$bidsdir" ] || [ -z "$ID_table" ] || [ -z "$input" ]; then
    echo "Error: Missing arguments"
    usage
fi

# Read the ID correspondence file and process each line
while IFS= read -r line || [[ -n "$line" ]]; do
    NEW_ID=$(echo "$line" | cut -f1)
    OLD_ID=$(echo "$line" | cut -f2)

    # Create directory for the new ID in the derivatives/Olea_perfusion folder
    mkdir -p "$bidsdir/derivatives/Olea_perfusion/sub-$NEW_ID/$session"

    # Run dcm2niix for the old ID's DICOM files
    dcm2niix -z y -f "%s_%d" -o "$bidsdir/derivatives/Olea_perfusion/sub-$NEW_ID/$session" "$input/$OLD_ID"
done < "$ID_table"

echo "Process completed."

