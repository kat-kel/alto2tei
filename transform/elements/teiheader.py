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
    unimarc_data, manifest_data = get_data(directory)
    teiheader = etree.SubElement(root, "teiHeader")
    filedesc = etree.SubElement(teiheader, "fileDesc")
    make_titlestmt(filedesc, unimarc_data, manifest_data)
    extent = etree.SubElement(filedesc, "extent")
    etree.SubElement(extent, "measure", unit="images", n=count_pages)
    make_publicationstmt(filedesc)
    make_souredesc(directory, filedesc, unimarc_data, manifest_data)
    make_profiledesc(teiheader, unimarc_data)
    return root


def make_titlestmt(filedesc, unimarc_data, manifest_data):
    """Create <titleStmt> and input relevant Unimarc data.

    Args:
        filedesc (etree): parsed <fileDesc> element of TEI file
        author_data (dict): each author's name(s), isni, and unique XML ID
        manifest_title (dict): document title according to IIIF manifest
    """    
    # {"author_isni":author_isni, "primary_name":primary_name, "secondary_name":secondary_name, "xmlid":xmlid}
    titlestmt = etree.SubElement(filedesc, "titleStmt")
    title = etree.SubElement(titlestmt, "title")
    if unimarc_data:
        title.text = unimarc_data["title"]
        if unimarc_data["authors"]:
            for a in unimarc_data["authors"]:
                author = etree.SubElement(titlestmt, "author", a["xmlid"])
                persname = etree.SubElement(author, "persName")
                if a["secondary_name"]:
                    forename = etree.SubElement(persname, "forename")
                    forename.text = a["secondary_name"]
                    if a["namelink"]:
                        namelink = etree.SubElement(persname,"nameLink")
                        namelink.text = a["namelink"]
                else:
                    namelink = etree.SubElement(persname,"nameLink")
                    namelink.text = a["namelink"]
                if a["primary_name"]:
                    surname = etree.SubElement(persname, "surname")
                    surname.text = a["primary_name"]
                if a["isni"] and a["isni"][:4] == "ISNI":
                    ptr = etree.SubElement(persname, "ptr")
                    ptr.attrib["type"] = "isni"
                    ptr.attrib["target"] = a["isni"][:4]
        titlestmt = resp_stmt(titlestmt)
    else:
        title.text = manifest_data["title"]
        if manifest_data["authors"]:
            for i, a in enumerate(manifest_data["authors"]):
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{a[:2]}{i}"}
                author = etree.SubElement(titlestmt, "author", xmlid)
                name = etree.SubElement(author, "name")
                name.text = a
    return titlestmt


def resp_stmt(titlestmt):
    """

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


def empty_sourcedesc(directory, filedesc, unimarc_data, manifest_data):
    sourcedesc = etree.SubElement(filedesc, "sourceDesc")
    bibl = etree.SubElement(sourcedesc, "bibl")
    ptr = etree.SubElement(bibl, "ptr")

    if unimarc_data:
        if unimarc_data["authors"]:
            for a in unimarc_data["authors"]:
                author = etree.SubElement(bibl, "author", a["xmlid"])
                persname = etree.SubElement(author, "persName")
                if a["secondary_name"]:
                    forename = etree.SubElement(persname, "forename")
                    forename.text = a["secondary_name"]
                    if a["namelink"]:
                        namelink = etree.SubElement(persname,"nameLink")
                        namelink.text = a["namelink"]
                else:
                    namelink = etree.SubElement(persname,"nameLink")
                    namelink.text = a["namelink"]
                if a["primary_name"]:
                    surname = etree.SubElement(persname, "surname")
                    surname.text = a["primary_name"]
    else:
        if manifest_data["authors"]:
            for i, a in enumerate(manifest_data["authors"]):
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{a[:2]}{i}"}
                author = etree.SubElement(bibl, "author", xmlid)
                name = etree.SubElement(author, "name")
                name.text = a

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
    country.attrib["key"]="FR"  # hard coded
    settlement = etree.SubElement(msidentifier, "settlement")
    settlement.text = "Paris"  # hard coded
    repository = etree.SubElement(msidentifier, "repository")
    repository.text = "Information not available."
    idno = etree.SubElement(msidentifier, "idno")
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


def make_souredesc(directory, filedesc, unimarc_data, manifest_data):
    elements = empty_sourcedesc(directory, filedesc, unimarc_data, manifest_data)
    if unimarc_data:
        if unimarc_data["title"]:
            elements["title"].text = unimarc_data["title"]
        else:
            elements["title"].text = manifest_data["title"]
        if unimarc_data["ptr"]:
            elements["ptr"].attrib["target"] = unimarc_data["ptr"]
        if unimarc_data["pubplace"]:
            elements["pubplace"].text = unimarc_data["pubplace"]
            if unimarc_data["pubplace_key"]:
                elements["pubplace"].attrib["key"] = unimarc_data["pubplace_key"]
        if unimarc_data["publisher"]:
            elements["publisher"].text = unimarc_data["publisher"]
        if unimarc_data["date"]:
            elements["d"].text = unimarc_data["date"]
        else:
            elements["d"].text = manifest_data["date"]
        if manifest_data["repository"]:
            elements["repository"].text = manifest_data["repository"]
        if unimarc_data["idno"]:
            elements["idno"].text = unimarc_data["idno"]
        if unimarc_data["objectdesc"]:
            elements["p"].text = unimarc_data["objectdesc"]
    else:
        elements["title"].text = manifest_data["title"]
        elements["pubplace"].text = None
        elements["pubplace"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["publisher"].text = None
        elements["publisher"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["d"].text = manifest_data["date"]
        elements["country"].text = None
        elements["country"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        elements["settlement"].text = None
        elements["settlement"].append(etree.Comment("Digitized source not found in institution's catalogue."))
        if manifest_data["repository"]:
            elements["repository"].text = manifest_data["repository"]
        else:
            elements["repository"].text = None
            elements["repository"].append(etree.Comment("Information not available."))
        if manifest_data["shelfmark"]:
            elements["idno"].text = manifest_data["shelfmark"]
        else:
            elements["idno"].text = None
            elements["idno"].append(etree.Comment("Information not available."))
        elements["p"].text = None
        elements["p"].append(etree.Comment("Digitized source not found in institution's catalogue."))


def make_profiledesc(teiheader, unimarc_data):
    profiledesc = etree.SubElement(teiheader, "profileDesc")
    langusage = etree.SubElement(profiledesc, "langUsage")
    if unimarc_data:
        if unimarc_data["lang"]:
            etree.SubElement(langusage, "language", ident=unimarc_data["lang"])
    else:
        etree.SubElement(langusage, "language", ident="")
