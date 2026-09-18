import requests

def test_search():
    url = "https://zeno-search.zeno.health/api/search?term=dolo&term_field=drug_name&search_type=drug_name&response_fields=composition%2Ctype%2Ccompany%2Cpack_value%2Cpack_uom&store_group_id=1&page_number=1&results_size=10&drug_status=Active%2CBanned%2CDiscontinued&source=zeno-app"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Data:")
        print(str(data)[:1000])
        
if __name__ == "__main__":
    test_search()
