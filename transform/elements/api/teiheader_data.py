import os
import re
from datetime import datetime

import requests
from lxml import etree

NS = {"s":"http://www.loc.gov/zing/srw/", "m":"info:lc/xmlns/marcxchange-v2"}


def get_data(directory):
    """Retrieve and synthesize metadata about a document.
    Args:
        directory (path): path to directory which contains document's pages
    Returns:
        data (dict): Unimarc data about authorship, Unimarc data about title, Unimarc data for <bibl>, Unimarc data for <profileDesc>
    """    
    request_for_document = RequestAPI(directory)

    # Get and clean data from IIIF manifest
    iiif_dict_response = request_for_document.iiif_manifest()
    manifest_data = ManifestData(iiif_dict_response).clean()
    
    # Get and clean data from BnF's SRU API
    sru_xml_response, perfect_match = request_for_document.sru_api(manifest_data["Catalogue ARK"])
    if perfect_match:
        raw_unimarc_data = UnimarcData(sru_xml_response)
        unimarc_data = raw_unimarc_data.clean()
    if not perfect_match:
        unimarc_data = None

    return manifest_data, unimarc_data


class RequestAPI:
    def __init__(self, directory):
        """Args:
            directory (paht): directory containing ALTO-encoded transcriptions of the document's pages"""
        self.directory = directory
    

    def iiif_manifest(self):
        """Request and clean metadata from the Gallica API.
        """   
        # Request manifest from Gallica API
        response = requests.get(f"https://gallica.bnf.fr/iiif/ark:/12148/{os.path.basename(self.directory)}/manifest.json/")
        raw_data = {d["label"]:d["value"] for d in response.json()["metadata"]}
        return raw_data


    def sru_api(self, ark):
        """Request metadata from the BnF's SRU API.
        Args:
            ark (str): the document's ARK in the BnF's catalogue
        Returns:
            root (etree_Element): parsed XML tree of requested Unimarc data
            perfect_match (boolean): True if request was completed with Gallica ark / directory basename
        """    
        print("|        requesting data from BnF's SRU API")
        r = requests.get(f'http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=(bib.persistentid all "{ark}")')
        root = etree.fromstring(r.content)
        if root.find('.//s:numberOfRecords', namespaces=NS).text=="0":
            perfect_match = False
            print(f"|        \33[31mdid not find digitised document in BnF catalogue\x1b[0m")
        else:
            perfect_match = True
            print(f"|        \33[32mfound digitised document in BnF catalogue\x1b[0m")
        return root, perfect_match


class ManifestData:
    def __init__(self, iiif_dict_response):
        self.raw_data = iiif_dict_response

    def clean(self):
        """Clean metadata received from Gallica API.
        Returns:
            clean_data (dict): cleaned data from IIIF manifest with values == None if not present in API request
        """        
        # Make defaultdict for cleaned metadata
        fields = ["Relation", "Catalogue ARK", "Repository", "Shelfmark", "Title", "Language", "Creator", "Date"]
        clean_data= {}
        {clean_data.setdefault(f, None) for f in fields}
        for k,v in self.raw_data.items():
            if type(v) is list and list(v[0].keys())[0]=="@value":
                clean_data[k]=v[0]["@value"]
            else:
                clean_data[k]=v
        # Derive catalogue ARK from "Relation" field; this will be used to access the BnF's SRU API
        if clean_data["Relation"]:
            clean_data["Catalogue ARK"]=(re.search(r"\/((?:ark:)\/\w+\/\w+)", clean_data["Relation"]).group(1))
        # Clean author name, getting rid of ". Auteur du texte" at the end of the string
        if clean_data["Creator"]:
            clean_data["Creator"]=re.search(r"(.+)(?:. Auteur du texte)", clean_data["Creator"]).group(1)
        return clean_data


class UnimarcData:
    def __init__(self, sru_xml_response):
        self.root = sru_xml_response


    def clean_authors(self):
        """Parses and cleans author data from Unimarc fields 701 and/or 702.
        Returns:
            data (dict): relevant authorship data (isni, surname, forename, xml:id)
        """        
        # if there is only one primary author
        data = []
        count = 0
        if self.root.find('.//m:datafield[@tag="700"]', namespaces=NS) is not None:
            author_element = self.root.find('.//m:datafield[@tag="700"]', namespaces=NS)
            count+=1
            data.append(self.author_data(author_element, count))
        if self.root.find('.//m:datafield[@tag="701"]', namespaces=NS) is not None:
            author_elements = self.root.findall('.//m:datafield[@tag="700"]', namespaces=NS)
            for element in author_elements:
                count+=1
                data.append(self.author_data(element, count))
        return data

    
    def author_data(self, author_element, count):
        """Create and fill datafields for relevant author data.
        Args:
            author_element (etree_Element): <mxc: datafield> being parsed
            count (int): author's count in processing
        Returns:
            data (dict) : relevant authorship data (isni, surname, forename, xml:id)
        """        
        # create and set defaults for author data
        fields = ["isni", "primary_name", "secondary_name", "namelink" , "xmlid"]
        data = {}
        {data.setdefault(f, None) for f in fields}
        
        # -- identifier (700s subfield "o") --
        has_isni = author_element.find('m:subfield[@code="o"]', namespaces=NS)
        if has_isni is not None and has_isni.text[0:4]=="ISNI":
            data["isni"] = has_isni.text[4:]

        # -- primary name (700s subfield "a") --
        has_primaryname = author_element.find('m:subfield[@code="a"]', namespaces=NS)
        if has_primaryname is not None:
            data["primary_name"] = has_primaryname.text

        # -- secondary name (700s subfield "b") --
        has_secondaryname = author_element.find('m:subfield[@code="b"]', namespaces=NS)
        if has_secondaryname is not None:
            x = re.search(r"(?:van der)|(?:de la)|(?:de)|(?:du)|(?:von)|(?:van)", has_secondaryname.text)
            if x:
                data["namelink"] = x.group(0)
            y = re.sub(r"(?:van der)|(?:de la)|(?:de)|(?:du)|(?:von)|(?:van)","", has_secondaryname.text)
            if y != "":
                data["secondary_name"] = y

        # -- unique xml:id for the author --
        if data["primary_name"]:
            name = data["primary_name"]
            data["xmlid"] = f"{name[:2]}{count}"
        elif data["secondary_name"]:
            data["xmlid"] = f"{name[:2]}{count}"
        else:
            data["xmlid"] = f"au{count}"
        
        return data


    def clean(self):
        """Parse and clean data from SRU API response.
        Returns:
            data (dict): all relevant metadata from BnF catalogue
        """        
        # create and set defaults for data
        fields = ["authors", "title", "ptr", "pubplace", "pubplace_key", "publisher", "date", "country", "idno", "objectdesc", "lang"]
        data = {}
        {data.setdefault(f, None) for f in fields}

        # enter author data into data dictionary
        data["authors"] = self.clean_authors()

        # enter cleaned title
        has_title = self.root.find('.//m:datafield[@tag="200"]/m:subfield[@code="a"]', namespaces=NS)
        if has_title is not None:
            data["title"] = has_title.text

        # enter link to the work in the institution's catalogue
        has_ptr = self.root.find('.//m:controlfield[@tag="003"]', namespaces=NS)
        if has_ptr is not None:
            data["ptr"] = has_ptr.text

        # enter publication place
        has_place = self.root.find('.//m:datafield[@tag="210"]/m:subfield[@code="a"]', namespaces=NS)
        if has_place is not None:
            data["pubplace"] = has_place.text

        # enter country code of publication place
        has_place_key = self.root.find('.//m:datafield[@tag="102"]/m:subfield[@code="a"]', namespaces=NS)
        if has_place_key is not None:
            data["pubplace_key"] = has_place_key.text

        # enter publisher
        has_publisher = self.root.find('.//m:datafield[@tag="210"]/m:subfield[@code="c"]', namespaces=NS)
        if has_publisher is not None:
            data["publisher"] = has_publisher.text

        # enter date of publication
        has_date = self.root.find('.//m:datafield[@tag="210"]/m:subfield[@code="d"]', namespaces=NS)
        if has_date is not None:
            data["date"] = has_date.text

        # enter country where the document is conserved
        has_country = self.root.find('.//m:datafield[@tag="801"]/m:subfield[@code="a"]', namespaces=NS)
        if has_country is not None:
            data["country"] = has_country.text

        # enter catalogue number of the document in the insitution
        has_isno = self.root.find('.//m:datafield[@tag="930"]/m:subfield[@code="a"]', namespaces=NS)
        if has_isno is not None:
            data["idno"] = has_isno.text

        # enter type of document (manuscript or print)
        has_objectdesc = self.root.find('.//m:datafield[@tag="200"]/m:subfield[@code="b"]', namespaces=NS)
        if has_objectdesc is not None:
            data["objectdesc"] = has_objectdesc.text

        # enter language of document
        has_lang = self.root.find('.//m:datafield[@tag="101"]/m:subfield[@code="a"]', namespaces=NS)
        if has_lang is not None:
            data["lang"] = has_lang.text

        return data
