import os
import re
from collections import defaultdict

from lxml import etree

NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # namespace for the Alto xml


def sourcedoc(ordered_files, dir, tei_root):
    """Creates the <sourceDoc> for an XML-TEI file using data parsed from a series of ALTO files.
        The <sourceDoc> collates each ALTO file, which represents one page of a document, into a wholistic
        description of the facsimile of the document.

    Args:
        ordered_files (list): names of ALTO files in the directory
        directory (path): path to document directory
        tei_root (etree._Element): etree element for the docuemnts'XML-TEI file
    """
    # get dictionary of tags from this document
    tag_dict = tags(ordered_files, dir)
    
    # create <sourceDoc> and its child <surfaceGrp>
    sourceDoc = etree.SubElement(tei_root, "sourceDoc")
    surfaceGrp = etree.SubElement(sourceDoc, "surfaceGrp")

    # -- SURFACE --
    # for every page in the document, create a <surface> and assign to it attributes derived from the ALTO file
    for file in ordered_files:
        folio = re.search(r"(.*f)(\d+)", file).group(2)  # get folio number from file name
        alto_root = etree.parse(f"{dir}/{file}").getroot()
        surface = etree.SubElement(surfaceGrp, "surface", page_attributes(alto_root, folio))
        
        # create <graphic> and assign its attributes
        etree.SubElement(surface, "graphic", url=f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(dir)}/f{folio}/full/full/0/native.jpg")

        # -- TEXTBLOCK --
        # for every <Page> in this ALTO file, create a <zone> for every <TextBlock> and assign the latter's attributes
        block_att, processed_blocks = zone_attributes(alto_root, dir, tag_dict, folio, "PrintSpace/", "TextBlock")
        lines_in_doc = 0
        for i in range(len(processed_blocks)):
            xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{folio}_z{i+1}"}
            text_block = etree.SubElement(surface, "zone", xml_id)
            for k,v in block_att[i].items():
                text_block.attrib[k]=v

            # -- TEXTLINE --
            # for every <TextBlock> in this ALTO file that has at least one <TextLine>, create a <zone> and assign its attributes
            text_line_att, processed_lines = zone_attributes(alto_root, dir, tag_dict, folio, f'TextBlock[@ID="{processed_blocks[i]}"]/', "TextLine")
            if len(processed_lines) > 0:                
                for j in range(len(processed_lines)):
                    xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{folio}_z{i+1}_l{j+1}"}
                    text_line = etree.SubElement(text_block, "zone", xml_id)
                    for k,v in text_line_att[j].items():
                        text_line.attrib[k]=v
                    lines_in_doc+=1
                    text_line.attrib["n"]=str(lines_in_doc)

                    # -- PATH --
                    xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{folio}_z{i+1}_l{j+1}_p"}
                    baseline = etree.SubElement(text_line, "path", xml_id)
                    b = alto_root.find(f'.//a:TextLine[@ID="{processed_lines[j]}"]', namespaces=NS).get("BASELINE")
                    baseline.attrib["points"] = " ".join([re.sub(r"\s", ",", x) for x in re.findall(r"(\d+ \d+)", b)])

                    # -- LINE --
                    # for every <TextLine> in this ALTO file that has a <String>, create a <line>
                    if alto_root.find(f'.//a:TextLine[@ID="{processed_lines[j]}"]/a:String', namespaces=NS).get("CONTENT") is not None:
                        xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{folio}_z{i+1}_l{j+1}t"}
                        string = etree.SubElement(text_line, "line", xml_id)
                        string.text = alto_root.find(f'.//a:TextLine[@ID="{processed_lines[j]}"]/a:String', namespaces=NS).get("CONTENT")
    return tei_root


def tags(ordered_files, dir):
    """Creates a dictionary of a tag's ID (key) and its LABEL (value).
        The IDs are unique to each document and must be recalculated for each directory.

    Args:
        ordered_files (list): list of file names in a directory ordered by folio number
        dir (path): path to document directory

    Returns:
        tags_dict (dict): tag-value pairs
    """    
    root = etree.parse(f"{dir}/{ordered_files[0]}").getroot()
    tags = [t.attrib for t in root.findall('.//a:OtherTag', namespaces=NS)]
    collect = defaultdict(dict)
    for d in tags:
        collect[d["ID"]] = d["LABEL"]
    tags_dict = dict(collect)
    return tags_dict


def page_attributes(root, folio):
    """Parses the ALTO file's <Page> attributes and synthesizes those data with 
        data from file paths to derive attributes for <surface> in the XML-TEI file.

    Args:
        root (etree._Element): etree of the ALTO file
        dir (path): path to document directory
        folio (string): folio number in ALTO file name

    Returns:
        page_attributes (dictionary): attributes to be applied to TEI <surface>
    """    
    att_list = root.find('.//a:Page', namespaces=NS).attrib
    page_attributes = {
        "{http://www.w3.org/XML/1998/namespace}id":f"f{folio}",
        "n":att_list["PHYSICAL_IMG_NR"],
        "ulx":"0",
        "uly":"0",
        "lrx":att_list["WIDTH"],
        "lry":att_list["HEIGHT"]
    }
    return page_attributes


def zone_attributes(alto_root, dir, tags, folio, parent, zone):
    """Parses attribute data from zone-like elements in ALTO file (TextBlock, TextLine) and prepares an attribute dictionary
        for a TEI <zone> element. It also records the ALTO @ID of the block processed which can be referenced later while 
        parsing data ALTO file to create the zone's children.

    Args:
        alto_root (etree._Element): etree of the ALTO file
        dir (path): path to document directory
        tags (dictionary): tag ID and LABEL for the document
        folio (string): folio number extracted from the ALTO file name
        parent (string): Xpath of the zone-like element's parent in the ALTO file
        zone (string): Xpath of the zone-like element in the ALTO file

    Returns:
        block_attributes (list): list of attribute dictionaries for each parsed zone-like element
        processed_blocks (list): list of @IDs for each parsed zone-like element
    """     
    zone_elements = [z for z in alto_root.findall(f'.//a:{parent}a:{zone}', namespaces=NS) \
                        if z.attrib['TAGREFS']!="BT" \
                        and z.attrib['TAGREFS']!="LT"]
                        # these conditions ignore any zone-like element whose tag is invalid
    att_list = [z.attrib for z in zone_elements]
    points = [z.find('.//a:Polygon', namespaces=NS).attrib for z in zone_elements]
    block_attributes = []
    processed_blocks = []
    for i in range(len(zone_elements)):
        tag_parts = re.match(r"(\w+):?(\w+)?#?(\d?)?", str(tags[att_list[i]["TAGREFS"]]))
        # the 3 groups of this regex parse the following expected tag syntax: MainZone:column#1 --> (MainZone)(column)(1)
        zone_points = " ".join([re.sub(r"\s", ",", x) for x in re.findall(r"(\d+ \d+)", points[i]["POINTS"])])
        x = att_list[i]["HPOS"]
        y = att_list[i]["VPOS"]
        w = att_list[i]["WIDTH"]
        h = att_list[i]["HEIGHT"]
        zone_att = {
            "type":tag_parts.group(1),
            "subtype":tag_parts.group(2) or "none",
            "n":tag_parts.group(3) or "none",
            "points":zone_points,
            "source":f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(dir)}/f{folio}/{x},{y},{w},{h}/full/0/native.jpg"
        }
        block_attributes.append(zone_att)
        processed_blocks.append(att_list[i]["ID"])
    return block_attributes, processed_blocks
    