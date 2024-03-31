import zipfile
import os
import tempfile
import shutil

from shutil import rmtree


def replace_and_save_document_xml(input_docx_path, output_docx_path, repace_files):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(input_docx_path, 'r') as docx:
        docx.extractall(temp_dir)

    for dst, src in repace_files.items():
        os.remove(os.path.join(temp_dir, dst))
        shutil.copy(src, os.path.join(temp_dir, dst))

    with zipfile.ZipFile(output_docx_path, 'w', zipfile.ZIP_DEFLATED) as docx:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                docx.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    rmtree(temp_dir)