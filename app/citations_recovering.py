from lxml import etree
from shutil import rmtree
from datetime import datetime
import zipfile
import os
import tempfile

from app.utils import Common, get, update


def get_document_xml(docx_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(docx_path, 'r') as docx:
        docx.extractall(temp_dir)

    with open(os.path.join(temp_dir, 'word/document.xml'), 'rb') as f:
        return f.read()


def replace_and_save_document_xml(input_docx_path, new_xml_path, output_docx_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(input_docx_path, 'r') as docx:
        docx.extractall(temp_dir)

    os.remove(os.path.join(temp_dir, 'word/document.xml'))
    os.rename(new_xml_path, os.path.join(temp_dir, 'word/document.xml'))

    with zipfile.ZipFile(output_docx_path, 'w', zipfile.ZIP_DEFLATED) as docx:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                docx.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    rmtree(temp_dir)


def get_content_for_begin(begin, namespace):
    current = begin.getparent()
    skip_ends = 0
    content = [current]
    while True:
        current = current.getnext()
        content.append(current)
        child = current[0]
        if child.tag.endswith("fldChar") and child.get("{"+namespace+"}fldCharType") == "begin":
            skip_ends += 1
        if child.tag.endswith("fldChar") and child.get("{"+namespace+"}fldCharType") == "end":
            if skip_ends > 0:
                skip_ends -= 1
            else:
                break  # this end related to this begin
    return content


class Worker(Common):
    async def run_citations_recovering(self, _):
        docx_with_broken_citations = await get('docx_with_broken_citations')
        docx_with_normal_citations = await get('docx_with_normal_citations')

        # get all begins with 'ADDIN EN.CITE' inside
        src_str = get_document_xml(docx_with_normal_citations)
        root = etree.fromstring(src_str)
        namespace = root.nsmap['w']
        begin_elements = root.xpath('//w:fldChar[@w:fldCharType="begin"]', namespaces=root.nsmap)

        wt2runs = {}
        for begin in begin_elements:
            try:
                content = get_content_for_begin(begin, namespace)
                content_as_txt = []
                for elem in content:
                    content_as_txt.append(etree.tostring(elem, method="text", encoding='unicode').strip())
                if 'ADDIN EN.CITE' not in content_as_txt:
                    continue

                wts = []
                for elem in content:
                    wts += elem.xpath('.//w:t', namespaces=root.nsmap)
                if len(wts) != 1:
                    raise Exception('more then 1 wt')
                wt = wts[0]
                wt2runs[wt.text] = content
            except:
                pass


        bibliography_form_src = []
        tmp = root.xpath('.//w:pStyle[@w:val="EndNoteBibliography"]', namespaces=root.nsmap)

        end = f'''<w:p xmlns:w="{namespace}">
            <w:r>
            <w:fldChar w:fldCharType="end"/>
            </w:r>
            </w:p>'''

        end = etree.fromstring(end)

        for item in tmp:
            wp = item.getparent().getparent()
            bibliography_form_src.append(wp)
        bibliography_form_src.append(end)


        dst_str = get_document_xml(docx_with_broken_citations)
        root = etree.fromstring(dst_str)
        wts = root.xpath('.//w:t', namespaces=root.nsmap)

        for wt in wts:
            if wt.text in wt2runs:
                wrs_to_insert = wt2runs[wt.text]
                wr = wt.getparent()
                wr_parent = wr.getparent()
                old_wr_index = wr_parent.index(wr)
                wr_parent.remove(wr)
                for offset, new_wr in enumerate(wrs_to_insert):
                    wr_parent.insert(old_wr_index + offset, new_wr)

        tmp = root.xpath('.//w:pStyle[@w:val="EndNoteBibliography"]', namespaces=root.nsmap)
        first_idx = None
        parent = None
        for elem in tmp:
            w_p = elem.getparent().getparent()
            parent = w_p.getparent()
            if first_idx is None:
                first_idx = parent.index(w_p)
            parent.remove(w_p)

        for offset, item in enumerate(bibliography_form_src):
            parent.insert(first_idx + offset, item)

        modified_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        new_document_xml = tempfile.NamedTemporaryFile(delete=False).name
        with open(new_document_xml, 'wb') as f:
            f.write(modified_str)

        tmp, ext = os.path.splitext(docx_with_normal_citations)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        output_docx_path = os.path.join(folder_path, f"{file_name}_{formatted_datetime}{ext}")

        replace_and_save_document_xml(
            docx_with_normal_citations,
            new_document_xml,
            output_docx_path
        )
        await update('last_docx_result', output_docx_path)
        await self.send_msg({
            'fn': 'update',
            'value': {
                'inProgress': False,
                'state.last_docx_result': output_docx_path
            }
        })
        await self.notify(f"Result in file {output_docx_path}")
