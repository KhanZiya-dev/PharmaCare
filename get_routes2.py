import re
data = open('main.dart.js', encoding='utf-8').read()
matches = re.findall(r'"(/productDetails[^"]*)"', data)
print(matches[:20])
matches2 = re.findall(r'"(/product/[^"]*)"', data)
print(matches2[:20])
