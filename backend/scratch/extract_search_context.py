import requests
import re

def extract():
    res = requests.get("https://www.zeno.health/main.dart.js")
    if res.status_code == 200:
        content = res.text
        # Find context around 'zeno-search'
        idx = content.find("zeno-search")
        if idx != -1:
            print(content[max(0, idx-100) : min(len(content), idx+200)])
        else:
            print("Not found")
            
        print("---")
        idx2 = content.find("search-service")
        if idx2 != -1:
             print(content[max(0, idx2-100) : min(len(content), idx2+200)])

if __name__ == "__main__":
    extract()
