import os
import xml.etree.ElementTree as ElementTree
ET = ElementTree

OUTPUT = os.path.join(os.getcwd(),'out')
VERSION = "2011"

class Constant(object):
    def __init__(self, xml, value=""):
        self.name = xml.findtext("name")
        self.description = xml.findtext("helpstring")
        self.value = xml.findtext("value")

        if self.value is None:
            self.value = value
        pass

    def toXML(self):
        element = ET.Element("constant")
        ET.SubElement(element, "name").text = self.name
        ET.SubElement(element, "value").text = str(self.value)
        ET.SubElement(element, "description").text = self.description
        return element

class Typedef(object):
    def __init__(self, xml):
        self.name = xml.findtext('name')
        self.version = VERSION
        self.constants = [Constant(x, i) for i, x in enumerate(xml.find('constants'))]

    def toXML(self):
        element = ET.Element("typedef")
        element.attrib["name"] = self.name
        element.attrib["version"] = self.version
        constants = ET.SubElement(element, "constants")
        [constants.append(x.toXML()) for x in self.constants]
        return element

class Parameter(object):
    def __init__(self, xml):
        self.type = xml.findtext('type')
        self.name = xml.findtext('name')
        self.attributes = [x.text for x in xml.find('attributes')]
        self.default = xml.findtext('attributes/defaultvalue')

        self.retval = 'out' in self.attributes
        self.optional = 'optional' in self.attributes or self.default is not None

    def toXML(self):
        element = ET.Element("parameter")
        if self.optional == True:
            element.attrib["optional"] = str(self.optional)
        ET.SubElement(element, "default").text = self.default
        ET.SubElement(element, "name").text = self.name
        ET.SubElement(element, "type").text = self.type
        return element

class Member(object):
    def __init__(self, xml):
        self.name = xml.findtext("name")
        self.description = xml.findtext("attributes/helpstring")
        self.parameters = [Parameter(x) for x in xml.find('parameters')]
        self.version = VERSION
        self.type = None

        self.attributes = [x.text for x in xml.find('attributes')]
        self.is_property = 'propput' in self.attributes or 'propget' in self.attributes


        for x in self.parameters:
            if x.retval == True:
                self.type = x.type

        self.parameters = [x for x in self.parameters if x.retval is False]

        if self.is_property and len(self.parameters) == 1:
            self.parameters = []

        syntax = self.type if self.type is not None else "void"
        syntax += " " + self.name

        if len(self.parameters) > 0:
            syntax += "(\n    "
            syntax += ",\n    ".join(
                ["{0} {1}".format(
                    x.type if x.type is not None else "void",
                    x.name
                ) for x in self.parameters]
            )
            syntax += "\n)"
        elif self.is_property is not True:
            syntax += "()"

        syntax += ";"

        self.syntax = [
            syntax
        ]


    def toXML(self):
        element = ET.Element("member")
        element.attrib["name"] = self.name
        element.attrib["version"] = self.version
        if self.is_property:
            element.attrib["type"] = "property"
        else:
            element.attrib["type"] = "method"

        returns_xml = ET.SubElement(element, "returns")
        type_xml = ET.SubElement(returns_xml, "type")
        type_xml.text = "void"
        if self.type is not None:
            type_xml.text = self.type

        ET.SubElement(element, "description").text = self.description

        def addSyntax(text):
            ET.SubElement(element, "syntax").text = text
        [addSyntax(x) for x in self.syntax]
        parameters = ET.SubElement(element, "parameters")
        [parameters.append(x.toXML()) for x in self.parameters if x.retval is False]
        return element

class Interface(object):
    def __init__(self, xml=None):
        if xml is not None:
            self.name = xml.findtext("name")
            self.description = xml.findtext("attributes/helpstring")
            self.version = VERSION
            self.members = {}

            definitions = xml.find("definitions")
            if definitions is not None:
                member = None
                for x in definitions.findall('function'):
                    self.addMember(x)

            methods = xml.find('methods')
            if methods is not None:
                for x in methods:
                    self.addMember(x)

            properties = xml.find('properties')
            if properties is not None:
                for x in properties:
                    self.addMember(x, True)

    def addMember(self, xml, is_property=False):
        member = Member(xml)

        if is_property is not False:
            member.is_property = True

        if member.name in self.members.keys():
            self.members[member.name] = self.combine_members(
                member,
                self.members[member.name]
            )
        else:
            self.members[member.name] = member

    def combine_members(self, m1, m2):
        temp = m1

        if m1.type is None and m2.type is not None:
            temp.type = m2.type
        if m2.type is None and m1.type is not None:
            temp.type = m1.type

        if m1.description != m2.description:
            temp.description = m1.description + "\n" + m2.description

        if len(m1.parameters) > len(m2.parameters):
            temp.parameters = m1.parameters
        else:
            temp.parameters = m2.parameters

        if (m1.syntax is not None and
            m2.syntax is not None and
            m1.syntax != m2.syntax):
            temp.syntax = m1.syntax + m2.syntax

        return temp

    def toXML(self):
        element = ET.Element("interface")
        element.attrib["name"] = self.name
        element.attrib["version"] = self.version
        ET.SubElement(element, "description").text = self.description
        members = ET.SubElement(element, "members")
        [members.append(self.members[x].toXML()) for x in self.members]
        return element

def combine(xml1, xml2):

    if xml2 is None:
        return xml1
    elif xml1 is None:
        return xml2

    root1 = xml1.getroot()
    root2 = xml2.getroot()

    if root1.tag != root2.tag:
        raise Exception("Root tag is not the same: {0} / {1}".format(root1.tag, root2.tag))

    temp = ET.Element(root1.tag)
    temp.attrib = dict(
        list(root1.attrib.items()) +
        list(root2.attrib.items())
    )

    for root in [root1, root2]:
        [temp.append(x) for x in root if len(x) > 0]

    return ET.ElementTree(temp)

def make_interface(xml, directory):
    interface_xml = Interface(xml)

    output_file = os.path.join(
        directory,
        interface_xml.name + ".xml"
    )

    tree = ET.ElementTree(interface_xml.toXML())
    if os.path.exists(output_file):
        tree = combine(tree, ET.parse(output_file))
    tree.write(output_file)

def make_typedef(xml, directory):
    typedef = Typedef(xml)

    output_file = os.path.join(
        directory,
        typedef.name + ".xml"
    )

    tree = ET.ElementTree(typedef.toXML())
    if os.path.exists(output_file):
        print(output_file)
        tree = combine(tree, ET.parse(output_file))

    tree.write(output_file)

def parse_definitions(xml, out_dir):
    if xml is not None:
        for interface in xml.findall('interface'):
            make_interface(interface, out_dir)

        for typedef in xml.findall('typedef'):
            make_typedef(typedef, out_dir)

def parse_xml(filename, output):
    root = ElementTree.parse(filename).getroot()
    out_dir = os.path.join(OUTPUT, output)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    parse_definitions(root, out_dir)
    parse_definitions(root.find('definitions'), out_dir)

    for element in root.findall('library'):
        parse_definitions(element.find('definitions'), out_dir)

def main():
    idls = [
        ('idl/cwmfc.idl.xml', 'CWCom'),
        ('idl/cv32old.idl.xml', 'CVScripting'),
        ('idl/cv32def.idl.xml', 'CVScripting/Enumerators'),
        ('idl/cv32Gateway.idl.xml', 'CVCom'),
        ('idl/enum.idl.xml', 'CWCom/Enumerators')
    ]
    for idl in idls:
        print(*idl)
        parse_xml(*idl)

if __name__ == '__main__':
    main()
