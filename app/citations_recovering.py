from lxml import etree
from datetime import datetime
import zipfile
import os
import tempfile

from app.utils import Common, get, update
from app.docx import replace_and_save_document_xml


def get_document_xml(docx_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(docx_path, 'r') as docx:
        docx.extractall(temp_dir)

    with open(os.path.join(temp_dir, 'word/document.xml'), 'rb') as f:
        return f.read()


def get_xmls_from_docx(docx_path, files):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(docx_path, 'r') as docx:
        docx.extractall(temp_dir)

    result = {}
    for file in files:
        path = os.path.join(temp_dir, file)
        if not os.path.exists(path):
            continue

        with open(path, 'rb') as f:
            result[file] = etree.fromstring(f.read())
    return result


def get_content_for_begin(begin, namespace):
    current = begin.getparent()
    skip_ends = 0
    content = [current]
    while True:
        current = current.getnext()
        content.append(current)
        stop = False
        for child in current.getchildren():
            if child.tag.endswith("fldChar") and child.get("{"+namespace+"}fldCharType") == "begin":
                skip_ends += 1
                break
            if child.tag.endswith("fldChar") and child.get("{"+namespace+"}fldCharType") == "end":
                if skip_ends > 0:
                    skip_ends -= 1
                else:
                    stop = True  # this end related to this begin
                    break
        if stop:
            break
    return content


class Worker(Common):
    async def run_citations_recovering(self, _):
        docx_with_broken_citations = await get('docx_with_broken_citations')
        docx_with_normal_citations = await get('docx_with_normal_citations')

        # get all begins with 'ADDIN EN.CITE' inside
        root = get_xmls_from_docx(docx_with_normal_citations, ['word/document.xml'])['word/document.xml']
        namespace = root.nsmap['w']
        begin_elements = root.xpath('//w:fldChar[@w:fldCharType="begin"]', namespaces=root.nsmap)

        wt2runs = {}
        for begin in begin_elements:
            try:
                content = get_content_for_begin(begin, namespace)
                citation = False
                for elem in content:
                    as_txt = etree.tostring(elem, method="text", encoding='unicode').strip()
                    if 'ADDIN EN.CITE' in as_txt:
                        citation = True
                        break
                if not citation:
                    continue

                wts = []
                for elem in content:
                    wts += elem.xpath('.//w:t', namespaces=root.nsmap)
                if len(wts) != 1:
                    continue
                wt = wts[0]
                wt2runs[wt.text] = content
            except:
                pass

        bibliography_form_src = []
        tmp = root.xpath('.//w:pStyle[@w:val="EndNoteBibliography"]', namespaces=root.nsmap)
        for item in tmp:
            wp = item.getparent().getparent()
            bibliography_form_src.append(wp)

        w_p_with_end = root.xpath('//w:fldChar[@w:fldCharType="end"]', namespaces=root.nsmap)[-1].getparent().getparent()
        bibliography_form_src.append(w_p_with_end)

        xmls = get_xmls_from_docx(docx_with_broken_citations, ['word/document.xml', 'word/_rels/document.xml.rels'])
        root = xmls['word/document.xml']
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
        parent = tmp[0].getparent().getparent().getparent()
        first_idx = None
        for elem in tmp:
            elem = elem.getparent().getparent()
            if first_idx is None:
                first_idx = parent.index(elem)
            parent.remove(elem)

        xml_rels = xmls['word/_rels/document.xml.rels']
        try:
            busy_ids = []
            for rel in xml_rels.getchildren():
                busy_ids.append(int(rel.attrib['Id'].replace('rId', '')))
            free_id = max(busy_ids) + 1
        except:
            pass

        rels = []
        for offset, item in enumerate(bibliography_form_src):
            links = item.xpath('.//w:hyperlink', namespaces=root.nsmap)
            if links:
                link = links[0]
                free_id_as_str = f"rId{free_id}"
                rels.append({
                    'url': link.xpath('.//w:t', namespaces=root.nsmap)[0].text,
                    'id': free_id_as_str
                })
                link.set('{' + root.nsmap['r'] + '}id', free_id_as_str)
                free_id += 1
            parent.insert(first_idx + offset, item)

        for rel in rels:
            Relationship = f'''<Relationship Id="{rel["id"]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="{rel['url']}" TargetMode="External"/>'''
            Relationship = etree.fromstring(Relationship)
            xml_rels.append(Relationship)

        xml_rels = etree.tostring(xml_rels, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        xml_rels_path = tempfile.NamedTemporaryFile(suffix='.xml', delete=False).name
        with open(xml_rels_path, 'wb') as f:
            f.write(xml_rels)

        modified_str = etree.tostring(root, pretty_print=True, xml_declaration=False, encoding='UTF-8')
        new_document_xml = tempfile.NamedTemporaryFile(suffix='.xml', delete=False).name
        with open(new_document_xml, 'wb') as f:
            f.write(modified_str)

        tmp, ext = os.path.splitext(docx_with_broken_citations)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        output_docx_path = os.path.join(folder_path, f"{file_name}_{formatted_datetime}{ext}")

        replace_and_save_document_xml(
            docx_with_broken_citations,
            output_docx_path,
            {
                'word/document.xml': new_document_xml,
                'word/_rels/document.xml.rels': xml_rels_path
            }
        )
        await update('last_docx_result', output_docx_path)
        await self.send_msg({
            'fn': 'update',
            'value': {
                'state.last_docx_result': output_docx_path
            }
        })
        await self.notify(f"Result in file {output_docx_path}")
