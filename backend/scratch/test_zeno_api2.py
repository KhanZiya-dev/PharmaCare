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
        
        print("Fetching categories...")
        r = requests.get("https://ecom.zeno.health/api/product-service/v1/product-categories/1/?store_group_id=2", headers=headers)
        if r.status_code == 200:
            print("Categories:")
            print(str(r.json())[:1000])

        # Test search again
        print("\nTesting search POST...")
        search_urls = [
            "https://ecom.zeno.health/api/product-service/v1/search",
            "https://ecom.zeno.health/api/product-service/v1/products/search",
            "https://ecom.zeno.health/api/search-service/v1/search",
        ]
        
        for url in search_urls:
            r = requests.post(url, headers=headers, json={"search": "paracetamol", "q": "paracetamol", "query": "paracetamol"})
            print(f"POST {url} -> {r.status_code}")
            if r.status_code == 200:
                print(str(r.json())[:500])
                break

if __name__ == "__main__":
    test_zeno()
