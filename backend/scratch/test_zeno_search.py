import requests
import json

def test_zeno():
    print("Fetching anonymous token...")
    res = requests.post("https://ecom.zeno.health/api/auth-service/v1/anonymous-user-login", json={"email":"fe1f98db-f2b8-4ec0-92cf-5dd212acdc1b@zeno.health"})
    
    if res.status_code == 200:
        data = res.json()
        token = data.get("data", {}).get("access_token")
        print("Token:", token)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        
        # Test zeno-search endpoints
        print("\nTesting zeno-search...")
        search_urls = [
            "https://zeno-search.zeno.health/search-service/v1/search?q=paracetamol",
            "https://zeno-search.zeno.health/search-service/v1/drug-search?q=paracetamol",
            "https://zeno-search.zeno.health/search-service/v1/search?keyword=paracetamol",
            "https://zeno-search.zeno.health/search-service/v1/drug-search", # POST
            "https://zeno-search.zeno.health/api/search-service/v1/search"
        ]
        
        for url in search_urls:
            r = requests.get(url, headers=headers)
            print(f"GET {url} -> {r.status_code}")
            if r.status_code == 200:
                print(str(r.json())[:500])
                
            if "drug-search" in url and "?" not in url:
                r2 = requests.post(url, headers=headers, json={"search": "paracetamol", "q": "paracetamol", "keyword": "paracetamol"})
                print(f"POST {url} -> {r2.status_code}")
                if r2.status_code == 200:
                    print(str(r2.json())[:500])
                

if __name__ == "__main__":
    test_zeno()
