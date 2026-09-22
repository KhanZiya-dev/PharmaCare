import os
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Load environment variables
load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    print("Fetching products...")
    products_res = supabase.table("products").select("id, name, category").execute()
    
    # Filter out lab tests
    medicines = [p for p in products_res.data if p.get("category") != "lab_test"]
    print(f"Total medicines found: {len(medicines)}")

    print("Fetching links...")
    links_res = supabase.table("platform_product_links").select(
        "product_id, platform_id, scrape_url"
    ).execute()

    platforms_res = supabase.table("platforms").select("id, name").execute()
    platform_map = {p["id"]: p["name"] for p in platforms_res.data}

    product_links = defaultdict(dict)
    for link in links_res.data:
        platform_name = platform_map.get(link["platform_id"], "Unknown")
        product_links[link["product_id"]][platform_name] = link["scrape_url"]

    medicines = sorted(medicines, key=lambda x: x["name"].lower())

    out_file = "d:/BSc.CS/Sem5/Pharmacare/Medicine_Testing_Batches.xlsx"
    batch_size = 30
    total_batches = (len(medicines) + batch_size - 1) // batch_size
    
    # Create Excel writer
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        for i in range(total_batches):
            batch = medicines[i*batch_size : (i+1)*batch_size]
            sheet_name = f"Batch_{i+1}"
            
            data = []
            for j, med in enumerate(batch):
                sno = (i * batch_size) + j + 1
                links = product_links.get(med["id"], {})
                
                # Excel HYPERLINK formula
                tata_url = links.get("Tata 1mg", "N/A")
                pe_url = links.get("PharmEasy", "N/A")
                apollo_url = links.get("Apollo Pharmacy", "N/A")
                
                tata_val = f'=HYPERLINK("{tata_url}", "Click Here")' if tata_url != "N/A" else "N/A"
                pe_val = f'=HYPERLINK("{pe_url}", "Click Here")' if pe_url != "N/A" else "N/A"
                apollo_val = f'=HYPERLINK("{apollo_url}", "Click Here")' if apollo_url != "N/A" else "N/A"
                
                data.append({
                    "S.No": sno,
                    "Medicine Name": med["name"],
                    "Tata 1mg Link": tata_val,
                    "1mg Correct? (Y/N)": "",
                    "PharmEasy Link": pe_val,
                    "PharmEasy Correct? (Y/N)": "",
                    "Apollo Link": apollo_val,
                    "Apollo Correct? (Y/N)": "",
                    "Notes/Comments": ""
                })
                
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Formatting
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Header format
            header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Set column widths
            col_widths = {'A': 6, 'B': 30, 'C': 15, 'D': 20, 'E': 15, 'F': 25, 'G': 15, 'H': 25, 'I': 30}
            for col, width in col_widths.items():
                worksheet.column_dimensions[col].width = width

    print(f"\nSuccessfully generated formatted Excel file: {out_file}")

if __name__ == "__main__":
    main()
