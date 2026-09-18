import requests
import json

def test_zeno():
    print("Fetching anonymous token...")
    # It might be a POST or GET
    res = requests.post("https://ecom.zeno.health/api/auth-service/v1/anonymous-user-login")
    if res.status_code != 200:
        res = requests.get("https://ecom.zeno.health/api/auth-service/v1/anonymous-user-login")
        
    print(res.status_code, res.text[:200])
    
    if res.status_code == 200:
        data = res.json()
        token = data.get("data", {}).get("access_token")
        print("Token:", token)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        
        print("Testing search for 'Paracetamol'...")
        # Guessing the search endpoint
        search_urls = [
            "https://ecom.zeno.health/api/product-service/v1/search?q=paracetamol",
            "https://ecom.zeno.health/api/product-service/v1/products/search?q=paracetamol",
            "https://ecom.zeno.health/api/product-service/v1/products?search=paracetamol"
        ]
        
        for url in search_urls:
            r = requests.get(url, headers=headers)
            print(f"URL: {url} -> {r.status_code}")
            if r.status_code == 200:
                print(str(r.json())[:500])
                break

if __name__ == "__main__":
    test_zeno()
