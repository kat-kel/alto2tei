from lxml import etree

def body(root):
    text = etree.SubElement(root, "text")
    body = etree.SubElement(text, "body")
    for page in root.findall('.//surface'):
        surface_id = ["{http://www.w3.org/XML/1998/namespace}id",page.get("{http://www.w3.org/XML/1998/namespace}id")]
        etree.SubElement(body, "pb", corresp=surface_id[1])
        for string in page.findall(f'.//line'):
            block = string.getparent().getparent().get("type")
            line = string.getparent().get("type")
            if block == "MainZone":
                if line == "DefaultLine":
                    l = etree.SubElement(body, "l", corresp=string.get("{http://www.w3.org/XML/1998/namespace}id"))
                    l.text = string.text



    return root