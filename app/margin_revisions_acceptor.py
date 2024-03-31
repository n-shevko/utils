import re
import zipfile
import os
import tempfile

from lxml import etree
from datetime import datetime

from app.utils import get, update
from app.docx import replace_and_save_document_xml
from app import citations_recovering


def get_xmls_to_accept(src_docx):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(src_docx, 'r') as docx:
        docx.extractall(temp_dir)

    word_folder = os.path.join(temp_dir, 'word')
    roots = {}
    for file in os.listdir(word_folder):
        if file in ['document.xml', 'styles.xml'] or re.match(r'footer\d+\.xml', file) or re.match(r'header\d+\.xml', file):
            path = os.path.join(word_folder, file)
            with open(path, 'rb') as f:
                roots[path] = etree.fromstring(f.read())
    return roots


def accept_all_revisions_on_margins(src_docx):
    roots = get_xmls_to_accept(src_docx)
    repace_files = {}
    tags = [
        '//w:rPrChange',
        '//w:pPrChange',

        '//w:del',

        '//w:tblPrChange',
        '//w:tcPrChange',
        '//w:trPrChange'
    ]
    for file, root in roots.items():
        for elem in root.xpath(' | '.join(tags), namespaces=root.nsmap):
            elem.getparent().remove(elem)
        modified_str = etree.tostring(root, pretty_print=True, xml_declaration=False, encoding='UTF-8')
        with open(file, 'wb') as f:
            f.write(modified_str)
        key = '/'.join(file.split('/')[-2:])
        repace_files[key] = file
    return repace_files


class Worker(citations_recovering.Worker):
    async def accept_revisions(self, _):
        docx_to_accept_revisions = await get('docx_to_accept_revisions')

        tmp, ext = os.path.splitext(docx_to_accept_revisions)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        output_docx_path = os.path.join(folder_path, f"{file_name}_{formatted_datetime}{ext}")

        replace_and_save_document_xml(
            docx_to_accept_revisions,
            output_docx_path,
            accept_all_revisions_on_margins(docx_to_accept_revisions)
        )
        await update('last_result_accept_revisions', output_docx_path)
        await self.send_msg({
            'fn': 'update',
            'value': {
                'state.last_result_accept_revisions': output_docx_path
            }
        })
        await self.notify(f"Result in file {output_docx_path}")

