# midl-to-xml
#
# Converts Microsoft IDL (MIDL) files to XML.
#
# Git Repository: https://github.com/jonathan-beckwith/midl-to-xml
#
# THE MIT LICENSE (MIT)
# Copyright (c) 2013 Jonathan Beckwith (jono.beckwith@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import os
import re
import pdb

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pyparsing import Word, Group, delimitedList, Literal, Keyword, Regex, \
    alphanums, nums, quotedString, SkipTo, restOfLine, OneOrMore, ZeroOrMore,\
    Optional, Forward, Suppress, cppStyleComment, hexnums, Combine, StringEnd,\
    ParseException, removeQuotes


def listFiles(root_path, ext):
    result = []
    for root, path, files in os.walk(root_path):
        result += [os.path.join(root, x) for x in files
                   if os.path.splitext(x)[1] == ext]

    return result


def parseIDL(text):

    definitions = Forward()

    #Quotation Mark Constants
    lbrack = Literal('{')
    rbrack = Literal('}')
    lbrace = Literal('[')
    rbrace = Literal(']')
    lparen = Literal('(')
    rparen = Literal(')')
    comma = Literal(',')
    dot = Literal('.')
    semicolon = Literal(';')
    colon = Literal(':')
    equals = Literal('=')
    minus = Literal('-')
    asterisk = Literal('*')

    stringLiteral = quotedString
    stringLiteral.setParseAction(removeQuotes)

    identifier = Word(alphanums + "_")

    #IDL Basic Types
    Boolean_ = Literal("Boolean")
    byte_ = Literal("byte")
    char_ = Literal("char")
    double_ = Literal("double")
    error_status_t_ = Literal("error_status_t")
    float_ = Literal("float")
    handle_t_ = Literal("handle_t")
    hyper_ = Literal("hyper")
    int_ = Literal("int")
    __int8_ = Literal("__int8")
    __int16_ = Literal("__int16")
    __int32_ = Literal("__int32")
    __int3264_ = Literal("__int3264")
    __int64_ = Literal("__int64")
    long_ = Literal("long")
    short_ = Literal("short")
    small_ = Literal("small")
    void_ = Literal("void")
    wchar_t_ = Literal("wchar_t")

    basetype = (
        Boolean_ |
        byte_ |
        char_ |
        double_ |
        error_status_t_ |
        float_ |
        handle_t_ |
        hyper_ |
        int_ |
        __int8_ |
        __int16_ |
        __int32_ |
        __int3264_ |
        __int64_ |
        long_ |
        short_ |
        small_ |
        void_ |
        wchar_t_
    )

    #COM Types
    type_specifier = Forward()

    struct_ = Keyword("struct")
    union_ = Keyword("union")
    enum_ = Keyword("enum")

    hresult_ = Keyword("HRESULT")
    variant_ = Keyword("VARIANT")
    variant_bool_ = Keyword("VARIANT_BOOL")
    bstr_ = Keyword("BSTR")
    safearray_ = Literal("SAFEARRAY") + lparen + type_specifier + rparen

    com_type = (
        hresult_ |
        variant_ |
        variant_bool_ |
        bstr_ |
        safearray_
    )

    #Type specifier - this can also be a user defined type (e.g. ICWAccount)
    type_specifier << (
        basetype |
        com_type |
        struct_ |
        union_ |
        enum_ |
        identifier) + Suppress(Optional(ZeroOrMore(asterisk)))

    uuid_ = Literal("uuid")
    uuid_number = Regex(r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-"
                        r"[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}")

    uuid = Suppress(uuid_ + lparen) + uuid_number("uuid") + Suppress(rparen)

    integer = Combine(Optional(minus) + Word(nums))
    hex_number = Regex(r"0x[A-Fa-f0-9]+")

    constant = hex_number | integer | stringLiteral

    version_ = Literal("version")
    version_number = (Combine(Word(nums) + dot + Word(nums)) | identifier)
    version = (
        Suppress(version_ + lparen) +
        version_number("version") +
        Suppress(rparen)
    )

    helpstring_ = Literal("helpstring")
    helpstring = Combine(
        Suppress(helpstring_ + lparen) +
        stringLiteral +
        Suppress(rparen)
    )

    plus_ = Literal('+')
    minus_ = Literal('-')
    multiply_ = Literal('*')
    divide_ = Literal('/')
    operator = (
        plus_ |
        minus_ |
        multiply_ |
        divide_
    )

    enum_modifier = operator + integer
    enum_definition = Group(
        Optional(
            Suppress(lbrace) +
            helpstring +
            Suppress(rbrace)
        ) +
        identifier("name") +
        Optional(
            Suppress(equals) +
            Combine(
                (constant | identifier) +
                Optional(enum_modifier)
            )("value")
        ) +
        Optional(Suppress(comma))
    )

    typedef_ = Keyword("typedef")
    typedef_attribute_list = (
        Suppress(lbrace) +
        delimitedList(identifier("value"), comma) +
        Suppress(rbrace)
    )

    #technically this could be a list of declarators
    #but that function is not used in the target IDL files.
    declarator_list = identifier  # #delimitedList(identifier, comma)

    typedef_header = (
        Suppress(typedef_) +
        Group(Optional(typedef_attribute_list))("attributes") +
        type_specifier("type") +
        declarator_list("name")
    )

    typedef = Group(
        typedef_header +
        Suppress(lbrack) +
        Group(ZeroOrMore(enum_definition("constant")))("constants") +
        Suppress(rbrack) +
        Suppress(declarator_list) +
        Suppress(semicolon)
    )

    dual_ = Keyword("dual")
    object_ = Keyword("object")
    ptr_ = Keyword("ptr")
    ref_ = Keyword("ref")
    unique_ = Keyword("unique")
    nonextensible_ = Keyword("nonextensible")
    default_ = Keyword("default")
    noncreatable_ = Keyword("noncreatable")
    hidden_ = Keyword("hidden")

    pointer_default_ = Literal("pointer_default")
    pointer_default = (
        Suppress(pointer_default_) +
        Suppress(lparen) +
        (ptr_ | ref_ | unique_) +
        Suppress(rparen)
    )

    helpcontext_ = Keyword("helpcontext")
    helpcontext = helpcontext_ + lparen + integer + rparen

    id_ = Keyword("id")
    com_id = (
        Suppress(id_) +
        Suppress(lparen) +
        identifier("id") +
        Suppress(rparen)
    )

    propget_ = Keyword("propget")
    propput_ = Keyword("propput")
    restricted_ = Keyword("restricted")

    function_attributes = (
        com_id |
        helpcontext |
        propget_ |
        propput_ |
        hidden_ |
        restricted_
    )("attribute")

    function_attribute = (
        helpstring("helpstring") |
        function_attributes
    )

    in_ = Keyword("in")("attribute")
    out_ = Keyword("out")("attribute")
    retval_ = Keyword("retval")("attribute")
    optional_ = Keyword("optional")("attribute")

    defaultvalue_ = Literal("defaultvalue")
    defaultvalue = (
        Suppress(defaultvalue_) +
        Suppress(lparen) +
        (constant | identifier) +
        Suppress(rparen)
    )("defaultvalue")

    arg_attributes = (
        in_ |
        out_ |
        retval_ |
        optional_
    )("attribute")

    arg_attribute = (
        arg_attributes |
        defaultvalue
    )

    arg_opts = (
        Suppress(lbrace) +
        delimitedList(arg_attribute, comma) +
        Suppress(rbrace)
    )

    function_arg = Group(
        Group(Optional(arg_opts))("attributes") +
        #Some functions have the arg_opts twice
        Suppress(Optional(arg_opts)) +
        type_specifier("type") +
        Optional(
            ZeroOrMore(asterisk) +
            identifier("name")
        )
    )("parameter")

    function_args = (
        Suppress(lparen) +
        Optional(delimitedList(function_arg, comma)) +
        Suppress(rparen)
    )

    function_opts = (
        Suppress(lbrace) +
        delimitedList(function_attribute, comma) +
        Suppress(rbrace)
    )
    function = Group(
        Group(Optional(function_opts))("attributes") +
        type_specifier("retval") +
        identifier("name") +
        Group(Optional(function_args))("parameters") +
        Suppress(semicolon)
    )("function")

    functions = ZeroOrMore(function)

    source_ = Keyword("source")
    oleautomation_ = Keyword("oleautomation")
    appobject_ = Keyword("appobject")

    #interface definition
    interface_ = Keyword("interface") | Keyword("dispinterface")
    interface_attributes = (
        uuid |
        helpcontext |
        version |
        dual_ |
        object_ |
        pointer_default |
        nonextensible_ |
        default_ |
        noncreatable_ |
        hidden_ |
        source_ |
        oleautomation_ |
        appobject_
    )("attribute")

    interface_attribute = (
        helpstring("helpstring") |
        interface_attributes
    )

    interface_opts = Group(
        Suppress(lbrace) +
        ZeroOrMore(interface_attribute + Suppress(Optional(comma))) +
        Suppress(rbrace))

    interface_body = (
        Suppress(lbrack) +
        Group(functions)("definitions") +
        Suppress(rbrack)
    )

    dispinterface_body = (
        Suppress(lbrack) +
        Suppress(Literal("properties:")) +
        Group(
            functions +
            Suppress(Literal("methods:")) +
            functions
        )("definitions") +
        Suppress(rbrack)
    )

    interface = Group(
        Optional(interface_opts)("attributes") +
        interface_("type") +
        identifier("name") +
        Optional(Suppress(colon) + identifier("base_class")) +
        Optional(interface_body | dispinterface_body) +
        Optional(Suppress(semicolon))
    )

    #COM coclass definition
    coclass_ = Keyword("coclass")
    coclass_attribute = (
        uuid |
        helpstring |
        noncreatable_ |
        hidden_ |
        appobject_
    )
    coclass_opts = ZeroOrMore(coclass_attribute + Suppress(Optional(comma)))

    coclass_head = Group(
        Suppress(lbrace) +
        coclass_opts +
        Suppress(rbrace)
    )
    coclass_body = (
        Suppress(lbrack) +
        definitions +
        Suppress(rbrack) +
        Suppress(semicolon)
    )
    coclass = (
        coclass_head("attributes") +
        coclass_("type") +
        identifier("name") +
        coclass_body
    )

    # COM Library definition
    library_ = Keyword("library")
    library_optional_attribute = (
        uuid |
        helpstring |
        version
    )

    library_options = Group(
        Suppress(lbrace) +
        ZeroOrMore(library_optional_attribute + Suppress(Optional(comma))) +
        Suppress(rbrace)
    )
    library_header = (
        library_options("attributes") +
        library_("type") +
        identifier("name")
    )
    library_body = (
        Suppress(lbrack) +
        Group(definitions)("definitions") +
        Suppress(rbrack)
    )

    library = Group(
        library_header +
        library_body +
        Suppress(semicolon)
    )

    definition = (
        library("library") |
        typedef("typedef") |
        coclass("coclass") |
        interface("interface")
    )
    definitions << ZeroOrMore(definition)
    IDL = definitions("definitions") + StringEnd()

    #ignore comments, preprocesser directives and imports
    comment = Literal('//') + restOfLine
    ml_comment_begin = Literal("/*")
    ml_comment_end = Literal("*/")
    ml_comment = (ml_comment_begin +
                  SkipTo(ml_comment_end) +
                  ml_comment_end)
    import_ = Literal('import') + restOfLine
    pp_if = Literal('#if') + restOfLine
    pp_endif = Literal('#endif') + restOfLine
    pp_else = Literal('#else') + restOfLine

    #Just ignore the second half of a conditional
    #this is a bit hacky but it should be OK for now.
    pp_conditional = pp_else + SkipTo(pp_endif) + (pp_endif)
    pp_include = Literal('#include') + restOfLine
    pp_define = Literal('#define') + restOfLine
    pp_directive = OneOrMore(pp_conditional | pp_include)
    midl_pragma_ = Keyword("midl_pragma")
    midl_pragma = midl_pragma_ + restOfLine

    IDL.ignore(import_)
    IDL.ignore(pp_define)
    IDL.ignore(comment)
    IDL.ignore(cppStyleComment)
    IDL.ignore(pp_conditional)
    IDL.ignore(pp_if)
    IDL.ignore(pp_endif)
    #IDL.ignore(pp_else)
    IDL.ignore(pp_include)
    IDL.ignore(midl_pragma)

    #IDL.enablePackrat()

    IDL("idl_file")
    tokens = IDL.parseString(text)

    #print(tokens)
    return tokens


def main():
    logger.setLevel(logging.DEBUG)

    idl_files = listFiles('idl', '.idl')

    for x in idl_files:
        tokens = []
        logger.debug(x)
        with open(x) as f:
            try:
                tokens = parseIDL(f.read())
                with open(x + '.xml', 'w') as result:
                    result.write(tokens.asXML())
            except ParseException as err:
                print(err)


if __name__ == '__main__':
    main()
