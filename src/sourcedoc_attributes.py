from lxml import etree
import re

NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # namespace for the Alto xml

class Attributes:
    def __init__(self, doc, folio, alto_root, tags):
        self.doc = doc
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
                "source":f"https://gallica.bnf.fr/iiif/ark:/12148/{self.doc}/f{self.folio}/{x},{y},{w},{h}/full/0/native.jpg"
            }
            block_attributes.append(zone_att)
            processed_blocks.append(att_list[i]["ID"])
        return block_attributes, processed_blocks