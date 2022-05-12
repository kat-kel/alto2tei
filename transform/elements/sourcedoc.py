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
        tei_root (etree._Element): etree element of the docuemnt's XML-TEI file
    Return:
        tei_root (etree._Element): etree element of the document's XML-TEI file, with <sourceDoc> completed
    """
    # get dictionary of tags for this document
    tags = DocTags(ordered_files[0], dir).labels()
    
    # create <sourceDoc> and its child <surfaceGrp>
    sourceDoc = etree.SubElement(tei_root, "sourceDoc")
    surfaceGrp = etree.SubElement(sourceDoc, "surfaceGrp")

    # for each ALTO file, instantiate its class Attributes and call the AltoFile's methods .folio() and .alto_root()
    # to get ALTO file's folio number (str) and XML tree root (etree._Element)
    for file in ordered_files:
        lines_on_page = 0
        folio = AltoFile(file, dir).folio
        alto_root = AltoFile(file, dir).alto_root
        attributes = Attributes(dir, folio, alto_root, tags)
        stree = SurfaceTree(dir, folio, alto_root)

        # -- SURFACE --
        # for every page in the document, create a <surface> and assign its attributes
        surface = stree.surface(surfaceGrp, attributes.surface())

        # -- TEXTBLOCK --
        # for every <Page> in this ALTO file, create a <zone> for every <TextBlock> and assign the latter's attributes
        textblock_atts, processed_textblocks = attributes.zone("PrintSpace/", "TextBlock")
        for textblock_count, processed_textblock in enumerate(processed_textblocks):
            text_block = stree.zone1(surface, textblock_atts, textblock_count)

            # -- TEXTLINE --
            # for every <TextBlock> in this ALTO file that has at least one <TextLine>, create a <zone> and assign its attributes
            textline_atts, processed_textlines = attributes.zone(f'TextBlock[@ID="{processed_textblock}"]/', "TextLine")
            if len(processed_textlines) > 0:
                for textline_count, processed_textline in enumerate(processed_textlines):
                    lines_on_page+=1
                    text_line = stree.zone2(lines_on_page, text_block, textblock_count, textline_atts, textline_count, processed_textline)

                    # -- LINE --
                    # for every <TextLine> in this ALTO file that has a <String>, create a <line>
                    if alto_root.find(f'.//a:TextLine[@ID="{processed_textline}"]/a:String', namespaces=NS).get("CONTENT") is not None:
                        stree.line(text_line, textblock_count, textline_count, processed_textline)
    return tei_root


class DocTags:
    """Creates a dictionary of a tag's ID (key) and its LABEL (value).
        The IDs are unique to each document and must be recalculated for each directory.
    """    
    def __init__(self, file, directory):
        self.file = file
        self.directory = directory
        
    def labels(self):
        root = etree.parse(f"{self.directory}/{self.file}").getroot()
        elements = [t.attrib for t in root.findall('.//a:OtherTag', namespaces=NS)]
        collect = defaultdict(dict)
        for d in elements:
            collect[d["ID"]] = d["LABEL"]
        self.tags = dict(collect)
        return self.tags


class AltoFile:
    def __init__(self, file, dir):
        self.file = file
        self.dir = dir
        self.folio = re.search(r"(.*f)(\d+)", self.file).group(2)  # get folio number from file name
        self.alto_root = etree.parse(f"{self.dir}/{self.file}").getroot()


class Attributes:
    def __init__(self, dir, folio, alto_root, tags):
        self.dir = dir
        self.folio = folio
        self.root = alto_root
        self.tags = tags

    def surface(self):
        att_list = self.root.find('.//a:Page', namespaces=NS).attrib
        attributes = {"{http://www.w3.org/XML/1998/namespace}id":f"f{self.folio}",
                    "n":att_list["PHYSICAL_IMG_NR"],
                    "ulx":"0",
                    "uly":"0",
                    "lrx":att_list["WIDTH"],
                    "lry":att_list["HEIGHT"]}
        return attributes

    def zone(self, parent, target):
        zone_elements = [z for z in self.root.findall(f'.//a:{parent}a:{target}', namespaces=NS) \
                        if 'TAGREFS' in z.attrib and\
                        z.attrib['TAGREFS']!="BT" \
                        and z.attrib['TAGREFS']!="LT"]
                        # these conditions ignore any zone-like element whose tag is invalid or which is missing @TAGREFS
        att_list = [z.attrib for z in zone_elements]
        points = [z.find('.//a:Polygon', namespaces=NS).attrib for z in zone_elements]
        block_attributes = []
        processed_blocks = []
        for i in range(len(zone_elements)):
            tag_parts = re.match(r"(\w+):?(\w+)?#?(\d?)?", str(self.tags[att_list[i]["TAGREFS"]]))
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
                "source":f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(self.dir)}/f{self.folio}/{x},{y},{w},{h}/full/0/native.jpg"
            }
            block_attributes.append(zone_att)
            processed_blocks.append(att_list[i]["ID"])
        return block_attributes, processed_blocks


class SurfaceTree:
    """Creates a <surface> element and its children for one page (ALTO file) of a document.
    """    
    def __init__(self, dir, folio, alto_root):
        self.dir = dir
        self.folio = folio
        self.root = alto_root

    def surface(self, surface_group, page_attributes):
        # -- surfaceGrp/surface-- 
        surface = etree.SubElement(surface_group, "surface", page_attributes)
        # create <graphic> and assign its attributes
        etree.SubElement(surface, "graphic", url=f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(self.dir)}/f{self.folio}/full/full/0/native.jpg")
        return surface

    def zone1(self, surface, textblock_atts, textblock_count):
        # -- surfaceGrp/surface/zone -- 
        xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{self.folio}_z{textblock_count+1}"}
        text_block = etree.SubElement(surface, "zone", xml_id)
        for k,v in textblock_atts[textblock_count].items():
            text_block.attrib[k]=v
        return text_block

    def zone2(self, lines_on_page, text_block, textblock_count, textline_atts, textline_count, processed_textline):    
        # -- surfaceGrp/surface/zone/zone --           
        zone_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{self.folio}_z{textblock_count+1}_l{textline_count+1}"}
        text_line = etree.SubElement(text_block, "zone", zone_id)
        for k,v in textline_atts[textline_count].items():
            text_line.attrib[k]=v
        text_line.attrib["n"]=str(lines_on_page)
        # -- surfaceGrp/surface/zone/zone --
        path_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{self.folio}_z{textblock_count+1}_l{textline_count+1}_p"}
        baseline = etree.SubElement(text_line, "path", path_id)
        b = self.root.find(f'.//a:TextLine[@ID="{processed_textline}"]', namespaces=NS).get("BASELINE")
        baseline.attrib["points"] = " ".join([re.sub(r"\s", ",", x) for x in re.findall(r"(\d+ \d+)", b)])
        return text_line

    def line(self, text_line, textblock_count, textline_count, processed_textline):
        # -- surfaceGrp/surface/zone/zone/line -- 
        xml_id = {"{http://www.w3.org/XML/1998/namespace}id":f"f{self.folio}_z{textblock_count+1}_l{textline_count+1}_t"}
        string = etree.SubElement(text_line, "line", xml_id)
        string.text = self.root.find(f'.//a:TextLine[@ID="{processed_textline}"]/a:String', namespaces=NS).get("CONTENT")
        return string
