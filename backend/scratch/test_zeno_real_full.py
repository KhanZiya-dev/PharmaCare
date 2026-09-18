import requests
import json

def test_search():
    url = "https://zeno-search.zeno.health/api/search?term=dolo&term_field=drug_name&search_type=drug_name&response_fields=composition%2Ctype%2Ccompany%2Cpack_value%2Cpack_uom&store_group_id=1&page_number=1&results_size=1&drug_status=Active%2CBanned%2CDiscontinued&source=zeno-app"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data['data'][0], indent=2))
        
if __name__ == "__main__":
    test_search()
