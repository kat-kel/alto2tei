import collections
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
    author_data = get_author(unimarc_xml)
    title_data = get_title(unimarc_xml)
    bib_data = get_bib(unimarc_xml)
    profile_data = get_profile(unimarc_xml)
    data = [author_data, title_data, bib_data, profile_data]
    return data, manifest_data, perfect_match


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
        r = requests.get(f'http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=(bib.title all "{manifest_data["manifest_title"]}")&maximumRecords=1')
        root = etree.fromstring(r.content)
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
    metadata = collections.deque(r.json()["metadata"])
    cat_ark = re.search(
        r"\/((?:ark:)\/\w+\/\w+)",
        [d for d in metadata if d["label"]=="Relation"][0]["value"])\
        .group(1)
    title = [d for d in metadata if d["label"]=="Title"][0]["value"]
    d = [d for d in metadata if d["label"]=="Date"][0]["value"]
    manifest_data = {"cat_ark": cat_ark, "manifest_title":title, "manifest_date":d}
    return manifest_data


def get_author(root):
    """Retrieve data about document's authorship from BNF API's Unimarc response.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        author_data (dict): relevant data about authorship (isni, surname, forename, xml:id)
    """    
    # if there is an author
    if root.find('.//m:datafield[@tag="700"]', namespaces=NS) is not None:
        authors = root.findall('.//m:datafield[@tag="700"]', namespaces=NS)
        author_data = []
        for i, author in enumerate(authors):
            has_id = author.find('m:subfield[@code="o"]', namespaces=NS)
            if has_id is not None:
                author_id = has_id.text
            else:
                author_id = None
            has_surname = author.find('m:subfield[@code="a"]', namespaces=NS)
            if has_surname is not None:
                author_surname = has_surname.text
            else:
                author_surname = None
            has_forename = author.find('m:subfield[@code="b"]', namespaces=NS)
            if has_forename is not None:
                author_forename = has_forename.text
            else:
                author_forename = None
            if author_surname:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{author_surname[:2]}{i}"}
            elif author_forename:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":f"{author_forename[:2]}{i}"}
            else:
                xmlid = {"{http://www.w3.org/XML/1998/namespace}id":"None"}
            author_data.append({"author_id":author_id, "author_surname":author_surname, "author_forename":author_forename, "id":xmlid})
    else:
        author_data = None
    return author_data


def get_title(root):
    """Retrieve data about document's titles from BNF API's Unimarc response.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        title_data (dict): relevant data about forms of the documents's title (uniform title, form title)
    """    
    # try to get uniform title
    has_uniform = root.find('.//m:datafield[@tag="500"]/m:subfield[@code="a"]', namespaces=NS)
    if has_uniform is not None:
        title_uniform = has_uniform.text
    else:
        title_uniform = None
    # try to get form title
    if root.find('.//m:datafield[@tag="503"]/m:subfield[@code="a"]', namespaces=NS) is not None:
        title_form = root.findall('.//m:datafield[@tag="503"]/m:subfield[@code="a"]', namespaces=NS)[-1].text
    else:
        title_form = None
    title_data = {"title_uniform":title_uniform, "title_form":title_form}
    return title_data


def get_bib(root):
    """Retrieve data from BNF API's Unimarc response relevant to <bibl> in XML-TEI.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        data (dict): data relevant to child elements of <bibl>
    """    

    # 608 -- type de document
    # 606 -- sujet de document

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
        pubplace_att = has_place_key.text
    else:
        pubplace_att = None
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

    # city where the document is conserved
    settlement = "Paris"
    #if root.find('', namespaces=NS) is not None:  <-- needs work
        #settlement = root.find('', namespaces=NS).text

    # institution where the document is conserved
    repository = "BNF"
    #if root.find('', namespaces=NS) is not None:  <-- needs work
        #repository = root.find('', namespaces=NS).text

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
    data = {
            "ptr":ptr,
            "pubplace":pubplace,
            "pubplace_att":pubplace_att,
            "publisher":publisher,
            "date":d,
            "country":country,
            "settlement":settlement,
            "repository":repository,
            "idno":idno,
            "objectdesc":objectdesc
        }
    return data


def get_profile(root):
    """Retrieve data about document's language from BNF API's Unimarc response.

    Args:
        root (etree): parsed XML tree of requested Unimarc data

    Returns:
        profile_data (dict): data relevant to <profileDesc> (language of document)
    """    
    has_lang = root.find('.//m:datafield[@tag="101"]/m:subfield[@code="a"]', namespaces=NS)
    if has_lang is not None:
        lang = has_lang.text
    else:
        lang = None
    profile_data = {"lang":lang}
    return profile_data
