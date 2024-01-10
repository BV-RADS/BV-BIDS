import os
import nibabel as nib
import matplotlib.pyplot as plt
import base64
import concurrent.futures
import glob
from io import BytesIO
import sys
from scipy import ndimage
import tempfile
import shutil

# Function to convert a matplotlib image to a data URI for embedding in HTML
def img_to_data_uri(img):
    rotated_img = ndimage.rotate(img, 90)
    img_buf = BytesIO()
    plt.imsave(img_buf, rotated_img, format='png', cmap='gray')
    img_buf.seek(0)
    data_uri = base64.b64encode(img_buf.read()).decode('utf-8')
    img_buf.close()
    return f"data:image/png;base64,{data_uri}"

# Function to extract the first volume from 4D NIfTI file
def extract_first_volume(file_path):
    img = nib.load(file_path)
    data = img.get_fdata()
    if len(data.shape) == 4:
        first_volume = data[:, :, :, 0]
        first_vol_img = nib.Nifti1Image(first_volume, img.affine)
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'temp.nii')
        nib.save(first_vol_img, temp_file_path)
        return temp_file_path, temp_dir
    return file_path, None

# Function to extract the middle slice from a NIfTI file
def get_middle_slice(file_path):
    img = nib.load(file_path)
    data = img.get_fdata()
    middle_slice = data[:, :, data.shape[2] // 2]
    return middle_slice

def process_subject(subject, sequences, BIDSDIR):
    subject_dir = os.path.join(BIDSDIR, subject)
    html_output = f"<tr><td>{subject}</td>"
    for seq in sequences:
        matched_files = glob.glob(f'{subject_dir}/**/*{seq}*.nii*', recursive=True)
        if len(matched_files) == 1:
            temp_file, temp_dir = extract_first_volume(matched_files[0])
            slice_img = get_middle_slice(temp_file)
            data_uri = img_to_data_uri(slice_img)
            html_output += f"<td><img src=\"{data_uri}\" style='width:auto; height:200px;'/></td>"
            if temp_dir:
                shutil.rmtree(temp_dir)
        elif len(matched_files) > 1:
            html_output += "<td>MULTI</td>"
        else:
            html_output += "<td>NONE</td>"
    html_output += "</tr>"
    return html_output

if len(sys.argv) < 2:
    print("Usage: python script.py <path_to_BIDSDIR>")
    sys.exit(1)

BIDSDIR = sys.argv[1]

if len(sys.argv) > 2:
    sequences = sys.argv[2:]
else:
    sequences = input("Enter sequences separated by space (e.g., t1w t2w flair t1c): ").split()

html_header = "<html><body><table><tr><th>Subject</th>"
for seq in sequences:
    html_header += f"<th>{seq}</th>"
html_header += "</tr>"

subjects = [d for d in os.listdir(BIDSDIR) if os.path.isdir(os.path.join(BIDSDIR, d)) and d.startswith('sub-')]
with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
    results = executor.map(lambda sub: process_subject(sub, sequences, BIDSDIR), subjects)




output_file_path = "BidsViewer_output.html"


try:
# Create an empty file or clear the existing file
    html_output = ""
    with open(output_file_path, "w") as file:
        pass
    # Process data
    html_output = html_header + "".join(results)
    html_output += "</table></body></html>"

    # Write the actual content
    with open(output_file_path, "w") as file:
        file.write(html_output)
    print("HTML file generated:", output_file_path)
except Exception as e:
    print("Error writing file:", e)

