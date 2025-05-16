import os
import zipfile

def unzip_file(zip_path):
    base_dir = os.path.dirname(zip_path)
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]  # 'testFigma'
    output_dir = os.path.join(base_dir, zip_name)
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir