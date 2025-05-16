import os
import base64
import zipfile
from PIL import Image

def unzip_file(zip_path):
    base_dir = os.path.dirname(zip_path)
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]  # 'testFigma'
    output_dir = os.path.join(base_dir, zip_name)
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir


def convert_to_base64(image_path):
    '''
    converts an image from a path into a base 64 string
    '''
    img = Image.open(image_path)    
    with open(image_path, "rb") as image_file:
        image_data = image_file.read() 
        base64_string = base64.b64encode(image_data).decode('utf-8')
    return base64_string
