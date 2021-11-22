#!/usr/bin/env python3

"""
Call json2xml from the command line:

    % ./json2xml.py tweet.json tweet | xmllint --format - > tweet.xml

or from a program:

    from json2xml import json2xml
    print(json2xml.Json2xml(data).to_xml())

"""

import sys
import json
from json2xml import json2xml
from json2xml.utils import readfromjson


if len(sys.argv) < 2:
      data = json.loads(sys.stdin.read())
else:
      data = readfromjson(sys.argv[1])

print(json2xml.Json2xml(data, wrapper="all", pretty=True, attr_type=False).to_xml())

