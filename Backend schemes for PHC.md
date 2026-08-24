# **Backend Database Schema Document**

**Project:** PharmaCare **Database Engine:** PostgreSQL (Hosted on Supabase) **Architecture:** Relational mapping \+ Time-series storage

## **1\. Core Tables & Data Types**

Humein system ko fast aur scalable rakhne ke liye 4 primary tables ki zaroorat padegi.

### **Table 1: products (The Master Catalog)**

Yeh table sirf dawai ya test ki basic information store karegi. Isme price nahi hoga.

| Column Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique identifier (Auto-generated). |
| name | VARCHAR(255) | NOT NULL | Product ka display name (e.g., "Pan-D Capsule"). |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | SEO-friendly URL (e.g., "pan-d-capsule"). |
| category | VARCHAR(50) | NOT NULL | medicine ya diagnostic. |
| composition | TEXT | NULLABLE | Salt details (Fuzzy search ke liye important). |
| requires\_rx | BOOLEAN | DEFAULT FALSE | True agar dawai Schedule H (prescription-only) hai. |
| image\_url | TEXT | NULLABLE | Master image URL. |
| created\_at | TIMESTAMP | DEFAULT NOW() | Record creation date. |

### **Table 2: platforms (The E-Pharmacies)**

Tumhare source websites ki list. Isko alag rakhne se kal ko naye competitors (jaise Netmeds) add karna aasan hoga.

| Column Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | SERIAL | PRIMARY KEY | Auto-incrementing ID (1, 2, 3...). |
| name | VARCHAR(100) | UNIQUE, NOT NULL | E.g., "Tata 1mg", "PharmEasy", "Apollo". |
| base\_url | VARCHAR(255) | NOT NULL | Website ka homepage. |
| logo\_url | TEXT | NULLABLE | Frontend pe logo render karne ke liye. |

### 

### **Table 3: platform\_product\_links (The Mapping Engine)**

**Yeh system ka sabse critical table hai.** Ek hi dawai ka page 1mg aur PharmEasy par alag hota hai. Yeh table scraper ko batati hai ki data kahan se lana hai.

| Column Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique mapping ID. |
| product\_id | UUID | FOREIGN KEY | Links to products.id (ON DELETE CASCADE). |
| platform\_id | INT | FOREIGN KEY | Links to platforms.id. |
| scrape\_url | TEXT | NOT NULL | Exact URL jahan Python script visit karegi. |
| affiliate\_url | TEXT | NULLABLE | Tumhara tracking link monetization ke liye. |
| last\_scraped | TIMESTAMP | NULLABLE | Script ko batata hai aakhiri update kab hua tha. |

### **Table 4: price\_history (Time-Series Log)**

Scraper har din yahan ek nayi entry karega. Yeh table rapidly grow karegi aur frontend ke chart ko data degi.

| Column Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique log ID. |
| mapping\_id | UUID | FOREIGN KEY | Links to platform\_product\_links.id. |
| mrp | DECIMAL(10,2) | NULLABLE | Original box price. |
| selling\_price | DECIMAL(10,2) | NOT NULL | Final discounted price. |
| discount\_pct | DECIMAL(5,2) | NULLABLE | Percentage saved. |
| in\_stock | BOOLEAN | DEFAULT TRUE | Availability status. |
| scraped\_at | TIMESTAMP | DEFAULT NOW() | Kis exact time par rate mila. |

## **2\. Relationships & Indexing (Speed Optimization)**

Agar hazaron dawaiyo ka mahino ka data hoga, toh database slow ho sakta hai. Use rokne ke liye hume yeh Indexes lagane honge:

> * **Search Optimization:** products table ke name aur composition column par **GIN Index (pg\_trgm)** lagayenge taaki typo-tolerant (fuzzy) search milliseconds mein kaam kare.  
> * **Time-Series Fetching:** price\_history table mein (mapping\_id, scraped\_at) par ek **Composite B-Tree Index** banega. Jab frontend pichle 30 din ka chart mangega, toh query is index se instantly resolve hogi.

## 

## **3\. Row Level Security (RLS) Policies**

Supabase ka security model RLS par based hai. Hum frontend aur backend ka access strictly define karenge:

> 1. **Frontend (Anon Key):**  
   * Can SELECT from products, platforms, and price\_history.  
   * **Cannot** INSERT, UPDATE, or DELETE.  
> 2. **Scraper/API (Service Role Key):**  
   * Has full Admin Access to INSERT new history logs and UPDATE the last\_scraped timestamp.

Is schema design se humaara system MVP se lekar hazaaron users tak scale hone ke liye ready hai.