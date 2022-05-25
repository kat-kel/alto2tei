from lxml import etree


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
            # instantiate class Line and collect data unique to this line (ln)
            line = Line(all_lines, ln, count)

            # if this is the document's first line 
            # or if this line comes from a page different than the preceding page, 
            # create a <pb>
            if count == 0 or line.this_page != line.previous_page:
                pb = etree.Element("pb", corresp=f"#{line.this_page}")
                div.append(pb)

            # create an empty <lb/> with this line's xmlid as @corresp
            lb = etree.Element("lb", line.att)
            
            # if this line's text comes from a zone for page numbers, quire marks, or running titles:
            if line.zone_type == "NumberingZone" or line.zone_type == "QuireMarksZone" or line.zone_type == "RunningTitleZone": 
                # enclose any page number, quire marks, or running title inside a <fw> 
                fw = etree.Element("fw", corresp=f"#{line.zone_id}", type=line.zone_type)
                div[-1].addnext(fw)
                fw.append(lb)
                lb.tail = ln.text
            
            # if this line's text come from marginalia:
            elif line.zone_type == "MarginTextZone":
                # create a <note> if one is not already the preceding sibling 
                if div[-1].tag != "note":
                    note = etree.Element("note", corresp=f"#{line.zone_id}", type=line.zone_type)
                    div[-1].addnext(note)
                    note.append(lb)
                # otherwise, append the margin text zone's line after the preceding sibling 
                else:
                    div[-1].append(lb)
                # in any case, add the line's text after the empty <lb>
                lb.tail = ln.text
            
            # if this line's text belongs to a main text zone:
            elif line.zone_type == "MainZone":
                # create an <ab> if one is not already the preceding sibling 
                if div[-1].tag != "ab":
                    ab = etree.Element("ab", corresp=f"#{line.zone_id}", type=line.zone_type)
                    ab.text = "\n"
                    div[-1].addnext(ab)
                #if this line's text is not a drop capital or a headling line:
                if line.type == "DropCapitalLine" or line.type == "HeadingLine":
                    elements_in_ab = [child for child in div[-1].getchildren()]
                    # create a <hi> if this is the <ab>'s first line / a <hi> is not already the preceding sibling
                    if len(elements_in_ab) == 0 or elements_in_ab[-1].tag != "hi":
                        hi = etree.Element("hi", rend=line.type)
                        hi.tail = "\n"
                        div[-1].append(hi)
                        hi.append(lb)
                    # otherwise append the <lb> directly after the preceding <hi> sibling
                    elif elements_in_ab[-1].tag== "hi":
                        elements_in_ab[-1].append(lb)
                    lb.tail = f"{ln.text}"
                # because this line's text is not a drop capital nor a headling line, 
                # append the text directly after the preceding sibling
                elif line.type == "DefaultLine":
                    div[-1].append(lb)
                    lb.tail = f"{ln.text}\n"

        return self.root


class Line:
    def __init__(self, lines, line, count):
        self.lines = lines
        self.line = line
        self.i = count
        id = self.line.getparent().get("{http://www.w3.org/XML/1998/namespace}id")
        self.att = {"corresp":f"#{id}"}
        self.type = self.line.getparent().get("type")
        self.zone_type = self.line.getparent().getparent().get("type")
        self.zone_id = self.line.getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
        self.this_page = self.line.getparent().getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
        self.previous_page = self.lines[self.i-1].getparent().getparent().getparent().get("{http://www.w3.org/XML/1998/namespace}id")
