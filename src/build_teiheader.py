# -----------------------------------------------------------
# Code by: Kelly Christensen
# Python script to assemble the <teiHeader> of a TEI file.
# -----------------------------------------------------------

from src.default_teiheader import DefaultTree
from src.full_teiheader import FullTree

NS = {"s":"http://www.loc.gov/zing/srw/", "m":"info:lc/xmlns/marcxchange-v2"}


def teiheader(metadata, document, root, count_pages):
    """Create all elements of the <teiHeader>.
    Args:
        document (str): name of directory containing ALTO-encoded transcriptions of the document's pages
        root (etree): XML-TEI tree
        count_pages (string): number of files in directory
    Returns:
        root (etree): XML-TEI tree
    """    
    
    # step 1 -- generate default <teiHeader>
    elements = DefaultTree(document, root, metadata, count_pages)  # deafult_teiheader.py
    elements.build()
    
    # step 2 -- enter available metadata into relevant element in <teiHeader>
    htree = FullTree(elements.children, metadata)  # full_teiheader.py
    htree.author_data()
    htree.other_data()
    return root
