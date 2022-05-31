from lxml import etree
from collections import namedtuple


class Text:
    def __init__(self, root):
        self.root = root
        self.data = self.line_data()

    def line_data(self):
        Line = namedtuple("Line", ["id", "n", "text", "line_type", "zone_type", "zone_id", "page_id"])
        data = [Line(
            ln.getparent().get("{http://www.w3.org/XML/1998/namespace}id"),  # @xml:id of the line's zone
            ln.getparent().get("n"),  # line number
            ln.text,  # text content of line
            ln.getparent().get("type"),  # @type of line
            ln.getparent().getparent().get("type"),  # @type of text block zone
            ln.getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id"),  # @xml:id of text block zone
            ln.getparent().getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id"),  # @xml:id of page
        ) for ln in self.root.findall('.//line')]
        return data
        