from lxml import etree
import os
from datetime import datetime
from collections import defaultdict, namedtuple

from .api.teiheader_data import get_data

NS = {"s":"http://www.loc.gov/zing/srw/", "m":"info:lc/xmlns/marcxchange-v2"}


def teiheader(directory, root, count_pages):
    """Create all elements of the <teiHeader>.
    Args:
        directory (path): path to directory containing ALTO-encoded transcriptions of the document's pages
        root (etree): XML-TEI tree
        count_pages (string): number of files in directory
    Returns:
        root (etree): XML-TEI tree
    """    
    manifest_data, unimarc_data = get_data(directory)

    # instantiate empty tree for this document's <teiHeader>
    elements = BlankTree(os.path.basename(directory), root, unimarc_data, manifest_data, count_pages)
    elements.build()
    
    # enter metadata
    htree = FullTree(elements.children, unimarc_data, manifest_data)
    htree.author_data()
    htree.other_data()

    return root


class FullTree:
    def __init__(self, children, unimarc_data, manifest_data):
        self.children = children
        self.catalogue = unimarc_data
        self.manifest = manifest_data

    def author_data(self):
        """Enter document's title and author into <titleStmt>.
        """        
        if self.catalogue:  # if the document's IIIF manifest had a valid catalogue ARK
            self.authors(self.children["titleStmt"], True, True)
        else:  # if the document's IIIF manifest didn't have a valid catalogue ARK
            self.authors(self.children["titleStmt"], False, True)

    def other_data(self):
        """Enter document's catalogue pointer (ptr), author, title, publication place, publisher, date into <bibl>.
            Enter institution's country code, settlement, repository name, shelfmark for the doc, and doc type into <msDesc>.
        """      
        Entry = namedtuple("Entry", ["tei_element","attribute","iiif_data","unimarc_data"])
        entries =   [Entry("ts_title",None,"Title","title"),
                    Entry("ptr","target",None,"ptr"),
                    Entry("bib_title",None,"Title","title"),
                    Entry("pubPlace",None,None,"pubplace"),
                    Entry("pubPlace","key",None,"pubplace_key"),
                    Entry("publisher",None,None,"publisher"),
                    Entry("date",None,"Date","date"),
                    Entry("country","key",None,"country"),
                    Entry("repository",None,"Repository",None),
                    Entry("idno",None,"Shelfmark","idno"),
                    Entry("p",None,None,"objectdesc"),
                    Entry("language",None,"Language",None),
                    Entry("language","ident",None,"lang")]
        for e in entries:
            if self.catalogue and e.unimarc_data and self.catalogue[e.unimarc_data]:
                self.entry(self.catalogue[e.unimarc_data], self.children[e.tei_element], e.attribute)
            elif e.iiif_data and self.manifest[e.iiif_data]:
                self.entry(self.manifest[e.iiif_data], self.children[e.tei_element], e.attribute)
    
    def entry(self, data, tei_element, attribute):
        if attribute:
            tei_element.attrib[attribute] = data
        else:
            tei_element.text = data

    def authors(self, parent, is_catologue_match, is_first_id):
        """Create elements about authorship in either fileDesc/titleStmt or fileDesc/sourceDesc/bibl.
        Args:
            parent (etree_Element): the parent element for the author data (<titleStmt> or <bibl>)
            is_catologue_match (boolean): True if the document's metadata was found in the BnF catalogue
            is_first_id (boolean): True if the author id is presented for the first time, aka "xml:id"
                                    if it's not the first time, the id will be "ref"
        """        
        if not parent.find('./author').text:  # if the default tree was not built for 0 authors and doesn't have default text
            xml_id = "{http://www.w3.org/XML/1998/namespace}id"
            if is_catologue_match:
                for count, author_root in enumerate(parent.findall('./author')):
                    if is_first_id:
                        author_root.attrib[xml_id] = self.catalogue["authors"][count]["xmlid"]
                    else:
                        author_root.attrib["ref"] = self.catalogue["authors"][count]["xmlid"]
                    persname = etree.SubElement(author_root, "persName")
                    if self.catalogue["authors"][count]["secondary_name"]:
                        forename = etree.SubElement(persname, "forename")
                        forename.text = self.catalogue["authors"][count]["secondary_name"]
                    if self.catalogue["authors"][count]["namelink"]:
                        namelink = etree.SubElement(persname,"nameLink")
                        namelink.text = self.catalogue["authors"][count]["namelink"]
                    if self.catalogue["authors"][count]["primary_name"]:
                        surname = etree.SubElement(persname, "surname")
                        surname.text = self.catalogue["authors"][count]["primary_name"]
                    if self.catalogue["authors"][count]["isni"]:
                        ptr = etree.SubElement(persname, "ptr")
                        ptr.attrib["type"] = "isni"
                        ptr.attrib["target"] = self.catalogue["authors"][count]["isni"]
            else:
                author_root = parent.find('./author')
                if self.manifest["Creator"] is not None:
                    a = self.manifest["Creator"]
                    if is_first_id:
                        author_root.attrib[xml_id] = f"{a[:2]}"
                    else:
                        author_root.attrib["ref"] = f"{a[:2]}"
                    name = etree.SubElement(author_root, "name")
                    name.text = a


class BlankTree:
    children = defaultdict(list)
    def __init__(self, directory, root, unimarc_data, manifest_data, count_pages):
        self.directory = directory
        self.root = root
        self.catalogue = unimarc_data
        self.manifest_data = manifest_data
        self.count = count_pages

    def build(self):
        if self.catalogue:
            default_text = "Information not available."
            num_authors = len(self.catalogue["authors"])
        else:
            default_text = "Digitised resource not found in BnF catalogue."
            num_authors = 1  # method of extracting IIIF manifest data will only return 1 author

        teiHeader = etree.SubElement(self.root, "teiHeader")
        fileDesc = etree.SubElement(teiHeader, "fileDesc")
        profileDesc = etree.SubElement(teiHeader, "profileDesc")
        titleStmt = etree.SubElement(fileDesc, "titleStmt")
        self.children["titleStmt"] = titleStmt
        self.children["ts_title"] = etree.SubElement(titleStmt, "title")  # pass to other methods
        self.children["ts_title"].text = default_text
        for i in range(num_authors):
            etree.SubElement(titleStmt, "author")
        if num_authors == 0:
            ts_author = etree.SubElement(titleStmt, "author")
            ts_author.text = default_text
        self.children["respStmt"] = etree.SubElement(titleStmt, "respStmt")  # pass to other methods (add: resp, persName)
        extent = etree.SubElement(fileDesc, "extent")
        etree.SubElement(extent, "measure", unit="images", n=self.count)
        self.children["publicationStmt"] = etree.SubElement(fileDesc, "publicationStmt")  # pass to other methods (add: publisher, authority, availability, date)
        sourceDesc = etree.SubElement(fileDesc, "sourceDesc")
        bibl = etree.SubElement(sourceDesc, "bibl")
        self.children["bibl"] = bibl
        self.children["ptr"] = etree.SubElement(bibl, "ptr")  # pass to other methods
        for i in range(num_authors):
            etree.SubElement(bibl, "author")
        if num_authors == 0:
            bib_author = etree.SubElement(titleStmt, "author")
            bib_author.text = default_text
        self.children["bib_title"] = etree.SubElement(bibl, "title")  # pass to other methods
        self.children["bib_title"].text = default_text
        self.children["pubPlace"] = etree.SubElement(bibl, "pubPlace")  # pass to other methods
        self.children["pubPlace"].text = default_text
        self.children["publisher"] = etree.SubElement(bibl, "publisher")  # pass to other methods
        self.children["publisher"].text = default_text
        self.children["date"] = etree.SubElement(bibl, "date")  # pass to other methods
        self.children["date"].text = default_text
        msDesc = etree.SubElement(sourceDesc, "msDesc")
        msIdentifier = etree.SubElement(msDesc, "msIdentifier")
        self.children["country"] = etree.SubElement(msIdentifier, "country")  # pass to other methods
        self.children["settlement"] = etree.SubElement(msIdentifier, "settlement")  # pass to other methods
        self.children["settlement"].text = default_text
        self.children["repository"] = etree.SubElement(msIdentifier, "repository")  # pass to other methods
        self.children["repository"].text = default_text
        self.children["idno"] = etree.SubElement(msIdentifier, "idno")  # pass to other methods
        self.children["idno"].text = default_text
        altIdentifer = etree.SubElement(msIdentifier, "altIdentifier")
        alt_idno = etree.SubElement(altIdentifer, "idno", type="ark")  # pass to other methods
        alt_idno.text = self.directory
        physDesc = etree.SubElement(msDesc, "physDesc")
        objectDesc = etree.SubElement(physDesc, "objectDesc")
        self.children["p"] = etree.SubElement(objectDesc, "p")  # pass to other methods
        self.children["p"].text = default_text
        langUsage = etree.SubElement(profileDesc, "langUsage")
        self.children["language"] = etree.SubElement(langUsage, "language") # pass to other methods
        self.children["language"].attrib["ident"] = ""
        self.HardCode().respstmt(self.children["respStmt"])
        self.HardCode().publicationstmt(self.children["publicationStmt"])

    class HardCode:
        def __init__(self):
            pass
        
        def respstmt(self, respstmt):
            editor1_forename = "Kelly"
            editor1_surname = "Christensen"
            editor1_orcid = "000000027236874X"
            respstmt.attrib["{http://www.w3.org/XML/1998/namespace}id"] = editor1_forename[0]+editor1_surname[0]
            resp = etree.SubElement(respstmt, "resp")
            resp.text = "transformation from ALTO4 to TEI by"
            editor_respstmt_persname = etree.SubElement(respstmt, "persName")
            editor_respstmt_forename = etree.SubElement(editor_respstmt_persname, "forename")
            editor_respstmt_forename.text = editor1_forename
            editor_respstmt_surname = etree.SubElement(editor_respstmt_persname, "surname")
            editor_respstmt_surname.text = editor1_surname
            editor_respstmt_ptr = etree.SubElement(editor_respstmt_persname, "ptr")
            editor_respstmt_ptr.attrib["type"] = "orcid"
            editor_respstmt_ptr.attrib["target"] = editor1_orcid

        def publicationstmt(self, publicationstmt):
            publisher = etree.SubElement(publicationstmt, "publisher")
            publisher.text = "Gallic(orpor)a"
            authority = etree.SubElement(publicationstmt, 'authority')
            authority.text = "BnF DATAlab"
            availability = etree.SubElement(publicationstmt, 'availability', status="restricted", n="cc-by")
            etree.SubElement(availability, "licence", target="https://creativecommons.org/licenses/by/4.0/")
            today = datetime.today().strftime('%Y-%m-%d')
            etree.SubElement(publicationstmt, "date", when=today)
