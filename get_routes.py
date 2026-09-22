import re
data = open('main.dart.js', encoding='utf-8').read()
routes = list(set(re.findall(r'"(/product[A-Za-z0-9_\/-]*)"', data)))
for r in routes[:50]:
    print(r)
