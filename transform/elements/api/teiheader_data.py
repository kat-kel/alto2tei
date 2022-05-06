import os
import re

import requests
from lxml import etree

NS = {"s":"http://www.loc.gov/zing/srw/", "m":"info:lc/xmlns/marcxchange-v2"}


def get_data(directory):
    """Call subsidiary functions and synthesize retrieved data in one dictionary.

    Args:
        directory (etree): path to directory containing ALTO-encoded transcriptions of the document's pages

    Returns:
        data (dict): Unimarc data about authorship, Unimarc data about title, Unimarc data for <bibl>, Unimarc data for <profileDesc>
    """    
    unimarc_xml, perfect_match, manifest_data = unimarc(directory)
    if perfect_match:
        unimarc_data = parse_unimarc(unimarc_xml)
    else:
        unimarc_data = None
    return unimarc_data, manifest_data


def unimarc(directory):
    """Request data from BNF's API.

    Args:
        directory (path): path to directory containing ALTO-encoded transcriptions of the document's pages

    Returns:
        root (etree): parsed XML tree of requested Unimarc data
        perfect_match (boolean): True if request was completed with Gallica ark / directory basename
        manifest_data (dict): saved data from searching IIIF manifest
    """    
    manifest_data = manifest(directory)
    r = requests.get(f'http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=(bib.persistentid all "{manifest_data["cat_ark"]}")')
    root = etree.fromstring(r.content)
    if root.find('.//s:numberOfRecords', namespaces=NS).text=="0":
        perfect_match = False
        print("|        did not find perfect match from Gallica ark")
    else:
        perfect_match = True
        print("|        found perfect match from Gallica ark")
    
    return root, perfect_match, manifest_data


def manifest(directory):
    """Request data from document's IIIF manifest.

    Args:
        directory (path): path to directory containing ALTO-encoded transcriptions of the document's pages

    Returns:
        manifest_data (dict): catalogue ark, title in the manifest, date in the manifest
    """    
    r = requests.get(f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(directory)}/manifest.json/")
    metadata = r.json()["metadata"]
    cat_ark = re.search(
        r"\/((?:ark:)\/\w+\/\w+)",
        [d for d in metadata if d["label"]=="Relation"][0]["value"])\
        .group(1)
    title = [d for d in metadata if d["label"]=="Title"][0]["value"]
    d = [d for d in metadata if d["label"]=="Date"][0]["value"]
    repo = [d for d in metadata if d["label"]=="Repository"][0]["value"]
    shelfmark = [d for d in metadata if d["label"]=="Shelfmark"][0]["value"]
    peeps = [d for d in metadata if d["label"]=="Creator"]
    authors = []
    for author in [a["value"] for a in peeps]:
        if "Auteur du texte" in author:
            author = re.search(r"(.+)(?:. Auteur du texte)", author).group(1)
            authors.append(author)
        else:
            authors.append(author)
    manifest_data = {"cat_ark": cat_ark, "title":title, "date":d, "repository":repo, "shelfmark":shelfmark, "authors":authors}
    return manifest_data


def parse_unimarc(root):
    """Extract relevant data from BNF API Unimarc response.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        data (dict):    list of authors, 1 title, 1 ptr, 1 pubPlace, 1 pubPlace country key, 1 publisher, 1 date of publication,
                        1 country of conservation, 1 shelfmark, 1 description of document type, 1 language of document
    """    
    # try to get authors
    authors = get_author(root)
    # try to get cleaned title
    has_title = root.find('.//m:datafield[@tag="200"]/m:subfield[@code="a"]', namespaces=NS)
    if has_title is not None:
        title = has_title.text
    else:
        title = None
    # link to the work in the institution's catalogue
    has_ptr = root.find('.//m:controlfield[@tag="003"]', namespaces=NS)
    if has_ptr is not None:
        ptr = has_ptr.text
    else:
        ptr = None
    # publication place
    has_place = root.find('.//m:datafield[@tag="210"]/m:subfield[@code="a"]', namespaces=NS)
    if has_place is not None:
        pubplace = has_place.text
    else:
        pubplace = None
    # country code of publication place
    has_place_key = root.find('.//m:datafield[@tag="102"]/m:subfield[@code="a"]', namespaces=NS)
    if has_place_key is not None:
        pubplace_key = has_place_key.text
    else:
        pubplace_key = None
    # publisher
    has_publisher = root.find('.//m:datafield[@tag="210"]/m:subfield[@code="c"]', namespaces=NS)
    if has_publisher is not None:
        publisher = has_publisher.text
    else:
        publisher = None
    # date of publication
    has_date = root.find('.//m:datafield[@tag="210"]/m:subfield[@code="d"]', namespaces=NS)
    if has_date is not None:
        d = has_date.text
    else:
        d = None
    # country where the document is conserved
    has_country = root.find('.//m:datafield[@tag="801"]/m:subfield[@code="a"]', namespaces=NS)
    if has_country is not None:
        country = has_country.text
    else:
        country = None
    # catalogue number of the document in the insitution
    has_isno = root.find('.//m:datafield[@tag="930"]/m:subfield[@code="a"]', namespaces=NS)
    if has_isno is not None:
        idno = has_isno.text
    else:
        idno = None
    # type of document (manuscript or print)
    has_objectdesc = root.find('.//m:datafield[@tag="200"]/m:subfield[@code="b"]', namespaces=NS)
    if has_objectdesc is not None:
        objectdesc = has_objectdesc.text
    else:
        objectdesc = None
    # language of document
    has_lang = root.find('.//m:datafield[@tag="101"]/m:subfield[@code="a"]', namespaces=NS)
    if has_lang is not None:
        lang = has_lang.text
    else:
        lang = None
    data = {
        "authors":authors,
        "title":title,
        "ptr":ptr,
        "pubplace":pubplace,
        "pubplace_key":pubplace_key,
        "publisher":publisher,
        "date":d,
        "country":country,
        "idno":idno,
        "objectdesc":objectdesc,
        "lang":lang
        }
    return data


def get_author(root):
    """Extract data about document's authorship from BNF API's Unimarc response.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        author_data (dict): relevant data about authorship (isni, surname, forename, xml:id)
    """    
    # if there is an author
    if root.find('.//m:datafield[@tag="700"]', namespaces=NS) is not None:
        peeps = root.findall('.//m:datafield[@tag="700"]', namespaces=NS)
        authors = []
        
        for i, author in enumerate(peeps):
            has_isni = author.find('m:subfield[@code="o"]', namespaces=NS)
            if has_isni is not None:
                author_isni = has_isni.text
            else:
                author_isni = None
            has_primaryname = author.find('m:subfield[@code="a"]', namespaces=NS)
            if has_primaryname is not None:
                primary_name = has_primaryname.text
            else:
                primary_name = None
            has_secondaryname = author.find('m:subfield[@code="b"]', namespaces=NS)
            if has_secondaryname is not None:
                m = re.search(r"(?:van der)|(?:de la)|(?:de)|(?:du)|(?:von)|(?:van)", has_secondaryname.text)
                if m:
                    namelink = m.group(0)
                else:
                    namelink = None
                secondary_name = re.sub(r"(?:van der)|(?:de la)|(?:de)|(?:du)|(?:von)|(?:van)","", has_secondaryname.text)
                if secondary_name == "":
                    secondary_name = None
            else:
                secondary_name = None
                namelink = None
            if primary_name:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{primary_name[:2]}{i}"}
            elif secondary_name:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{primary_name[:2]}{i}"}
            else:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"au{i}"}
            authors.append({"isni":author_isni, "primary_name":primary_name, "secondary_name":secondary_name, "namelink":namelink, "xmlid":xmlid})
    else:
        authors = None
    return authors
