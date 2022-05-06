from lxml import etree
import os
from datetime import datetime

from .api.teiheader_data import get_data

NS = {"s":"http://www.loc.gov/zing/srw/", "m":"info:lc/xmlns/marcxchange-v2"}


def teiheader(directory, root, count_pages):
    """Create all elements of the <teiHeader>.

    Args:
        directory (path): path to directory containing ALTO-encoded transcriptions of the document's pages
        root (etree): XML tree
        count_pages (string): number of files in directory

    Returns:
        root (etree): XML tree
    """    
    data, manifest_data, perfect_match = get_data(directory)
    teiheader = etree.SubElement(root, "teiHeader")
    filedesc = etree.SubElement(teiheader, "fileDesc")
    make_titlestmt(filedesc, data[0], manifest_data["manifest_title"])
    extent = etree.SubElement(filedesc, "extent")
    etree.SubElement(extent, "measure", unit="images", n=count_pages)
    make_publicationstmt(filedesc)
    make_souredesc(directory, filedesc, data[0], data[1], data[2], manifest_data, perfect_match)
    make_profiledesc(teiheader, data[3])
    return root


def make_titlestmt(filedesc, author_data, manifest_title):
    """Retrieve data from parsed Unimarc XML and input it into TEI tree.

    Args:
        filedesc (etree): parsed <fileDesc> element of TEI file
        author_data (dict): each author's name(s), isni, and unique XML ID
        manifest_title (dict): document title according to IIIF manifest
    """    
    titlestmt = etree.SubElement(filedesc, "titleStmt")
    title = etree.SubElement(titlestmt, "title")
    title.text = manifest_title
    if author_data:
        for i in range(len(author_data)):
            author = etree.SubElement(titlestmt, "author", author_data[i]["id"])
            persname = etree.SubElement(author, "persName")
            if author_data[i]["author_forename"]:
                forename = etree.SubElement(persname, "forename")
                forename.text = author_data[i]["author_forename"]
            if author_data[i]["author_surname"]:
                surname = etree.SubElement(persname, "surname")
                surname.text = author_data[i]["author_surname"]
            if author_data[i]["author_id"][:4] == "ISNI":
                ptr = etree.SubElement(persname, "ptr")
                ptr.attrib["type"] = "isni"
                ptr.attrib["target"] = author_data[i]["author_id"][4:]
    titlestmt = resp_stmt(titlestmt)
    return titlestmt


def resp_stmt(titlestmt):
    """_summary_

    Args:
        titlestmt (_type_): _description_
    """    
    editor1_forename = "Kelly"
    editor1_surname = "Christensen"
    editor1_orcid = "000000027236874X"
    respstmt = etree.SubElement(titlestmt, "respStmt")
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


def make_publicationstmt(filedesc):
    publicationstmt = etree.SubElement(filedesc, "publicationStmt")
    publisher = etree.SubElement(publicationstmt, "publisher")
    publisher.text = "Gallic(orpor)a"
    authority = etree.SubElement(publicationstmt, 'authority')
    authority.text = "BnF DATAlab"
    availability = etree.SubElement(publicationstmt, 'availability', status="restricted", n="cc-by")
    etree.SubElement(availability, "licence", target="https://creativecommons.org/licenses/by/4.0/")
    today = datetime.today().strftime('%Y-%m-%d')
    etree.SubElement(publicationstmt, "date", when=today)


def empty_sourcedesc(directory, filedesc, author_data):
    sourcedesc = etree.SubElement(filedesc, "sourceDesc")
    bibl = etree.SubElement(sourcedesc, "bibl")
    ptr = etree.SubElement(bibl, "ptr")

    if author_data:
            for i in range(len(author_data)):
                author = etree.SubElement(bibl, "author")
                persname = etree.SubElement(author, "persName")
                if author_data[i]["author_forename"]:
                    forename = etree.SubElement(persname, "forename")
                    forename.text = author_data[i]["author_forename"]
                if author_data[i]["author_surname"]:
                    surname = etree.SubElement(persname, "surname")
                    surname.text = author_data[i]["author_surname"]

    title = etree.SubElement(bibl, "title")
    title.text = "Information not available."
    pubplace = etree.SubElement(bibl, "pubPlace")
    pubplace.text = "Information not available."
    publisher = etree.SubElement(bibl, "publisher")
    publisher.text = "Information not available."
    d = etree.SubElement(bibl, "date")
    d.text = "Information not available."
    msdesc = etree.SubElement(sourcedesc, "msDesc")
    msidentifier = etree.SubElement(msdesc, "msIdentifier")
    country = etree.SubElement(msidentifier, "country")
    settlement = etree.SubElement(msidentifier, "settlement")
    settlement.text = "Information not available."
    repository = etree.SubElement(msidentifier, "repository")
    repository.text = "Information not available."
    idno = etree.SubElement(msidentifier, "idno")  # côte dans le catalogue
    altidentifier = etree.SubElement(msidentifier, "altIdentifier", type="ark")
    ark_idno = etree.SubElement(altidentifier, "idno")
    ark_idno.text = os.path.basename(directory)
    physdesc = etree.SubElement(msdesc, "physDesc")
    objectdesc = etree.SubElement(physdesc, "objectDesc")
    p = etree.SubElement(objectdesc, "p")
    p.text = "Information not available."
    elements = {
        "bibl":bibl,
        "ptr":ptr,
        "title":title,
        "pubplace":pubplace,
        "publisher":publisher,
        "d":d,
        "country":country,
        "settlement":settlement,
        "repository":repository,
        "idno":idno,
        "p":p
    }
    return elements


def make_souredesc(directory, filedesc, author_data, title_data, bib_data, manifest_data, perfect_match):
    elements = empty_sourcedesc(directory, filedesc, author_data)
    if title_data["title_uniform"]:
        elements["title"].text = title_data["title_uniform"]
    else:
        elements["title"].text = manifest_data["manifest_title"]
    if perfect_match:
        if bib_data["ptr"]:
            elements["ptr"].attrib["target"] = bib_data["ptr"]
        if bib_data["pubplace"]:
            elements["pubplace"].text = bib_data["pubplace"]
            if bib_data["pubplace_att"]:
                elements["pubplace"].attrib["key"] = bib_data["pubplace_att"]
        if bib_data["publisher"]:
            elements["publisher"].text = bib_data["publisher"]
        if bib_data["date"]:
            elements["d"].text = bib_data["date"]
        else:
            elements["d"].text = manifest_data["manifest_date"]
        if bib_data["country"]:
            elements["country"].attrib["key"] = bib_data["country"]
        if bib_data["settlement"]:
            elements["settlement"].text = bib_data["settlement"]
        if bib_data["repository"]:
            elements["repository"].text = bib_data["repository"]
        if bib_data["idno"]:
            elements["idno"].text = bib_data["idno"]
        if bib_data["objectdesc"]:
            elements["p"].text = bib_data["objectdesc"]
    else:
        elements["pubplace"].text = None
        elements["pubplace"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["publisher"].text = None
        elements["publisher"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["d"].text = manifest_data["manifest_date"]
        elements["country"].text = None
        elements["country"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["settlement"].text = None
        elements["settlement"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["repository"].text = None
        elements["repository"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["idno"].text = None
        elements["idno"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["p"].text = None
        elements["p"].append(etree.Comment("Digitized source not found in institution's catalogue."))


def make_profiledesc(teiheader, data):
    profiledesc = etree.SubElement(teiheader, "profileDesc")
    langusage = etree.SubElement(profiledesc, "langUsage")
    if data["lang"]:
        etree.SubElement(langusage, "language", ident=data["lang"])
    else:
        language = etree.SubElement(langusage, "language")
        language.append(etree.Comment("Information not available"))