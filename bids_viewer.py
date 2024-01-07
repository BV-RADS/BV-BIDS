import os
import nibabel as nib
import matplotlib.pyplot as plt
import base64
import concurrent.futures
import glob
from io import BytesIO
import sys

# Function to convert a matplotlib image to a data URI for embedding in HTML
def img_to_data_uri(img):
    img_buf = BytesIO()
    plt.imsave(img_buf, img, format='png', cmap='gray')  # Save the image to a buffer
    img_buf.seek(0)
    data_uri = base64.b64encode(img_buf.read()).decode('utf-8')  # Encode as base64
    img_buf.close()
    return f"data:image/png;base64,{data_uri}"

# Function to extract the middle slice from a NIfTI file
def get_middle_slice(file_path):
    img = nib.load(file_path)  # Load the NIfTI file
    data = img.get_fdata()  # Get the data from the file
    middle_slice = data[:, :, data.shape[2] // 2]  # Extract the middle slice
    return middle_slice

# Function to process a subject directory
def process_subject(subject, sequences, BIDSDIR):
    subject_dir = os.path.join(BIDSDIR, subject)
    html_output = f"<tr><td>{subject}</td>"
    for seq in sequences:
        # Find all files matching the sequence in the subject directory
        matched_files = glob.glob(f'{subject_dir}/**/*{seq}*.nii*', recursive=True)
        # Process according to the number of matching files
        if len(matched_files) == 1:
            slice_img = get_middle_slice(matched_files[0])
            data_uri = img_to_data_uri(slice_img)
            html_output += f"<td><img src=\"{data_uri}\"/></td>"
        elif len(matched_files) > 1:
            html_output += "<td>MULTI</td>"
        else:
            html_output += "<td>NONE</td>"
    html_output += "</tr>"
    return html_output

# Check if the path to BIDSDIR is provided as a command line argument
if len(sys.argv) < 2:
    print("Usage: python script.py <path_to_BIDSDIR>")
    print("\nThis script is designed to process MRI sequences in a BIDS-formatted dataset.")
    print("It generates an HTML file displaying middle axial slices of specified MRI sequences for each subject.")
    print("\n<path_to_BIDSDIR> should be the path to the directory containing the BIDS-structured neuroimaging dataset.")
    print("After running the script, you will be prompted to enter the names of the MRI sequences you wish to visualize (e.g., t1w t2w flair t1c).")
    print("\nThe output will be an HTML file named 'output.html', which will contain a table with the middle axial slices for each sequence and subject.")
    sys.exit(1)



# Set the BIDSDIR from the first command line argument
BIDSDIR = sys.argv[1]

# Check if sequences are provided as command line arguments; if not, prompt the user
if len(sys.argv) > 2:
    sequences = sys.argv[2:]
else:
    sequences = input("Enter sequences separated by space (e.g., t1w t2w flair t1c): ").split()



# Prepare the HTML table header
html_header = "<html><body><table><tr><th>Subject</th>"
for seq in sequences:
    html_header += f"<th>{seq}</th>"
html_header += "</tr>"

# Process each subject directory in parallel using multiple threads
subjects = [d for d in os.listdir(BIDSDIR) if os.path.isdir(os.path.join(BIDSDIR, d)) and d.startswith('sub-')]
with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
    results = executor.map(lambda sub: process_subject(sub, sequences, BIDSDIR), subjects)

# Combine the results into the final HTML
html_output = html_header + "".join(results)
html_output += "</table></body></html>"

# Save the HTML output to a file
with open("output.html", "w") as file:
    file.write(html_output)

print("HTML file generated: output.html")

