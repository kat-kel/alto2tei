import os
import re
import sys
from datetime import datetime

from lxml import etree

from elements.sourcedoc import sourcedoc
from elements.teiheader import teiheader
from elements.body import body

NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # XML-ALTO namespace


def order_files(dir):
    """Creates a numerically ordered list of file names from the given directory path.
        This resolves any issue with file names ordered in the directory alphabetically.
        For example, it corrects ["file_f10", "file_f9"] to ["file_f9", "file_f10"].

    Args:
        dir (path): path to directory containing ALTO-encoded transcriptions of the document's pages
    
    Returns:
        ordered_files (list): file names from directory ordered by folio number
    """
    file_names = [file for file in os.listdir(dir) if file.endswith(".xml")]
    folio_numbers = sorted([int(re.search(r"(.*f)(\d+)", file).group(2)) for file in file_names])
    prefix = re.search(r"(.*f)(\d+)", file_names[0]).group(1)
    ordered_files = [prefix+str(number)+".xml" for number in folio_numbers]
    return ordered_files


def make_tei(ordered_files, directory):
    """Creates an XML-TEI file for one document. The document's pages must be encoded in XML-ALTO v. 4 and
        assembled in one directory which has the same name as the document's ARK. (ex. 'bpt6k10516302/')

    Args:
        ordered_files (list): names of ALTO files in the directory
        directory (path): path to directory containing ALTO-encoded transcriptions of the document's pages
    """    
    print("=====================================")
    print(f"\33[32m~ now processing {os.path.basename(directory)} ~\x1b[0m")

    # -- TEI --
    tei_root_att = {"xmlns":"http://www.tei-c.org/ns/1.0", "{http://www.w3.org/XML/1998/namespace}id":f"ark_12148_{os.path.basename(directory)}"}
    root = etree.Element("TEI", tei_root_att)
    
    # -- TEIHEADER --
    print(f"\33[33mcreating <teiHeader>\x1b[0m")
    t0 = datetime.utcnow()
    root = teiheader(directory, root, str(len(ordered_files)))
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds")
    
    # -- SOURCEDOC --
    print(f"\33[33mcreating <sourceDoc>\x1b[0m")
    t0 = datetime.utcnow()
    root = sourcedoc(ordered_files, directory, root)
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds")
    print("")

    # -- BODY --
    print(f"\33[33mcreating <body>\x1b[0m")
    t0 = datetime.utcnow()
    root = body(root)
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds")
    print("")
    
    with open(f'data/{os.path.basename(directory)}.xml', 'wb') as f:
        etree.ElementTree(root).write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directories = [path for path in sys.argv[1:] if os.path.isdir(path)]  # create a list of directories in data/*
        for directory in directories:  # create XML-TEI file for each directory / document
            ordered_files = order_files(directory)
            make_tei(ordered_files, directory)
    else:
        print("No directory given")
