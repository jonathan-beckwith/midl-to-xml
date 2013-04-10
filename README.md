midl-to-xml
===========

Converts Microsoft IDL (MIDL) files to XML using pyparsing.

This grammar only handles a subset of IDL (only the parts I needed), but it should work as a starting point for expansion.

MIDL grammar definition is available here: [MSDN: MIDL Language Reference](http://msdn.microsoft.com/en-us/library/windows/desktop/aa367088.aspx)

Requirements
------------

- [pyparsing](http://pyparsing.wikispaces.com/)
- Python 3.x (may work in Python 2.7, but I haven't tested it)


Usage
-----

Add a directory named 'idl' to the same directory as this script, and run it. The script will scan the idl directory for any files with a .idl extension and convert them to .xml files, saving them in the xml subfolder.

License
-------

> The MIT License (MIT)

> Copyright (c) 2013 Jonathan Beckwith

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

> **The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.**

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.