import sys
import json
from json2xml import json2xml
from json2xml.utils import readfromjson


if len(sys.argv) < 2:
      data = json.loads(sys.stdin.read())
else:
      data = readfromjson(sys.argv[1])

print(json2xml.Json2xml(data).to_xml())

