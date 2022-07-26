<<<<<<< HEAD
=======
# -----------------------------------------------------------
# Code by: Kelly Christensen
# Python class to assemble the main elements of a TEI file.
# -----------------------------------------------------------

from src.iiif_data import IIIF_API
from src.sru_data import SRU_API
from src.build_teiheader import teiheader
from src.build_sourcedoc import sourcedoc
from src.build_body import body
from src.segment import segment
from src.text_data import Text
from src.tags_dict import Tags
>>>>>>> main
from lxml import etree
from src.teiheader_metadata.clean_data import Metadata
from src.teiheader_build import teiheader
from src.sourcedoc_build import sourcedoc
from src.text_data import Text
from src.body_build import body

class TEI:
    metadata = {"sru":None, "iiif":None}
    tags = {}
    root = None
    segmonto_zones = None
    segmonto_lines = None
    def __init__(self, document, filepaths):
        self.d = document  # (str) this document's name / name of directory contiaining the ALTO files
        self.fp = filepaths  # (list) paths of ALTO files
        self.metadata  # (dict) dict with two keys ("iiif", "sru"), each of which is equal to its own dictionary of metadata
        self.tags  # (dict) a label-ref pair for each tag used in this document's ALTO files
        self.root  # (etree_Element) root for this document's XML-TEI tree
<<<<<<< HEAD
        self.segmonto_zones
        self.segmonto_lines


=======
    
   # -- PHASE 1 -- metadata preparation
    def prepare_data(self):
        """Parse data from APIs and ALTO files to prepare dictionaries of document data.
            The value of self.metadata's key "iiif" is updated from None to the dictionary that the SRU_API.clean() method returns.
            The value of self.metadata's key "sru" isupdated from None to the dictionary that the SRU_API.clean() method returns.
            The dictionary self.tags is reassigned to a dictionary that the Tags.labels() method returns.
        """   

        # -- Parse data from IIIF Image API --     
        iiif = IIIF_API(self.d)  # (iiif_data.py) instantiate a IIIF_API class for this document
        iiif_data = iiif.clean(iiif.request())  # get the IIIF Image API's JSON response
        self.metadata.update({"iiif":iiif_data})  # parse the JSON response and prepare dictionary of relevant data
        # -- Parse data from BnF's SRU API --
        sru = SRU_API(iiif_data["Catalogue ARK"])  # (sru_data.py) isntantiate an SRU_API class for this document
        response, perfect_match = sru.request()  # get the BnF SRU API's MARCXML response and/or a boolean confirming if the document was found
        sru_data = sru.clean(response, perfect_match)  # parse the MARCXML response and prepare dictinoary of relevant data
        self.metadata.update({"sru":sru_data})
        # -- Parse tag data from one ALTO document --
        self.tags = Tags(self.p[0], self.d, self.NS).labels()  # (tags_dict.py) get dictionary of tags {label:ref} for this document
    
    # -- PHASE 2 -- XML-TEI construction of <teiHeader> and <sourceDoc>
>>>>>>> main
    def build_tree(self):
        """Parse and map data from ALTO files to an XML-TEI tree's <teiHeader> and <sourceDoc>.
        """   

        # instantiate the XML-TEI root for this document and assign the root basic attributes
        tei_root_att = {"xmlns":"http://www.tei-c.org/ns/1.0", "{http://www.w3.org/XML/1998/namespace}id":f"ark_12148_{self.d}"}
        self.root = etree.Element("TEI", tei_root_att)
    
<<<<<<< HEAD
    def build_header(self, config, version):
        # confirm that the metadata is being récupéré
        self.metadata = Metadata(self.d, config["iiifURI"]).prepare()
        self.root, self.segmonto_zones, self.segmonto_lines = teiheader(self.metadata, self.d, self.root, len(self.fp), config, version, self.fp, self.segmonto_zones, self.segmonto_lines)
    
    def build_sourcedoc(self, config):
        sourcedoc(self.d, self.root, self.fp, self.tags, self.segmonto_zones, self.segmonto_lines, config["iiifURI"])

    def build_body(self):
=======
    # -- PHASE 3 -- extract and annotate text in <body> and <standoff>
    def annotate_text(self):
        """Parse and map data from the <souceDoc> to XML-TEI elements in <body>.
        """      
          
>>>>>>> main
        text = Text(self.root)
        body(self.root, text.data)
