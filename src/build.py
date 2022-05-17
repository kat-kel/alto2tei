from src.iiif_data import IIIF_API
from src.sru_data import SRU_API
from src.build_teiheader import teiheader
from src.build_sourcedoc import sourcedoc
from src.annotate_body import Body
from src.tags_dict import Tags
from lxml import etree

class XMLTEI:
    metadata = {"sru":None, "iiif":None}
    tags = {}
    root = None
    NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # namespace for the Alto xml
    def __init__(self, document, filepaths):
        self.d = document
        self.p = filepaths
        self.metadata
        self.tags
        self.root
    
   # -- phase 1 -- metadata preparation
    def prepare_data(self):
        iiif = IIIF_API(self.d)  # iiif_data.py
        iiif_data = iiif.clean(iiif.request())
        self.metadata.update({"iiif":iiif_data})
        #----------------------------------------
        sru = SRU_API(iiif_data["Catalogue ARK"])  # sru_data.py
        response, perfect_match = sru.request()
        sru_data = sru.clean(response, perfect_match)
        self.metadata.update({"sru":sru_data})
        #----------------------------------------
        # get dictionary of tags for this document
        self.tags = Tags(self.p[0], self.d, self.NS).labels()  # tags_dict.py
    
    # -- phase 2 -- XML-TEI construction of <teiHeader> and <sourceDoc>
    def build_tree(self):
        tei_root_att = {"xmlns":"http://www.tei-c.org/ns/1.0", "{http://www.w3.org/XML/1998/namespace}id":f"ark_12148_{self.d}"}
        self.root = etree.Element("TEI", tei_root_att)
        # build <teiHeader>
        teiheader(self.metadata, self.d, self.root, len(self.p))  # build_teiheader.py
        # build <sourceDoc>
        sourcedoc(self.d, self.root, self.p, self.tags)  # build_sourcedoc.py
    
    # -- phase 3 -- extract and annotate text in <body>
    def annotate_body(self):
        body = Body(self.tags, self.root, self.NS)
        body.build()
        