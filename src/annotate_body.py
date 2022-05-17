from lxml import etree
from collections import namedtuple
import re

class Body:
    def __init__(self, tags, root, namespace):
        self.tags = tags
        self.root = root
        self.ns = namespace

    def build(self):
        text = etree.SubElement(self.root, "text")
        body = etree.SubElement(text, "body")
        div = etree.SubElement(body, "div")
        all_lines = self.root.findall('.//line', self.ns)

        for count, ln in enumerate(all_lines):
            line = Line(all_lines, ln, count)

            if count == 0 or line.this_page != line.previous_page:
                pb = etree.Element("pb", corresp=f"#{line.this_page}")
                div.append(pb)

            # append line's text to empty line beginning element <lb>
            lb = etree.Element("lb", line.att)
            
            
            if line.zone_type == "NumberingZone" or line.zone_type == "QuireMarksZone" or line.zone_type == "RunningTitleZone": 
                fw = etree.Element("fw", corresp=f"#{line.zone_id}", n=line.zone_type)
                div[-1].addnext(fw)
                fw.append(lb)
                lb.tail = ln.text
            
            elif line.zone_type == "MarginTextZone":
                note = etree.Element("note", corresp=f"#{line.zone_id}", n=line.zone_type)
                div[-1].addnext(note)
                note.append(lb)
                lb.tail = ln.text
            
            elif line.zone_type == "MainZone":
                if div[-1].tag != "p":
                    p = etree.Element("p", corresp=f"#{line.zone_id}", n=line.zone_type)
                    p.text = "\n"
                    div[-1].addnext(p)
                if line.type == "DropCapitalLine" or line.type == "HeadingLine":
                    hi = etree.Element("hi", n=line.type)
                    hi.tail = "\n"
                    div[-1].append(hi)
                    hi.append(lb)
                    lb.tail = f"{ln.text}"
                elif line.type == "DefaultLine":
                    div[-1].append(lb)
                    lb.tail = f"{ln.text}\n"
        return self.root


class Line:
    def __init__(self, lines, line, count):
        self.lines = lines
        self.line = line
        self.i = count
        id = self.line.get("{http://www.w3.org/XML/1998/namespace}id")
        self.att = {"corresp":f"#{id}"}
        self.type = self.line.getparent().get("type")
        self.zone_type = self.line.getparent().getparent().get("type")
        self.zone_id = self.line.getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
        self.this_page = self.line.getparent().getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
        self.previous_page = self.lines[self.i-1].getparent().getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
