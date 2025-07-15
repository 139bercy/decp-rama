import re

pattern = r'^[A-Za-z0-9/\-_ .#]{1,16}$'

res = re.match(pattern=pattern,string="202423MG###010")
print(res)