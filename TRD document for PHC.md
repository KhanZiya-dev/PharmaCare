#  **Requirements Document (TRD)**

**Project Name:** PharmaCare **Document Version:** 2.0 (MVP Finalized) **Architecture:** Microservices-based (Frontend, API API, Scraper Worker)

## **1\. System Architecture Overview**

System ko teen isolated layers mein divide kiya gaya hai taaki scalability aur security maintain rahe:

> 1. **Frontend (Client Layer):** User interface jahan search, comparison aur rendering hogi.  
> 2. **API Layer (Backend):** Frontend aur Database ke beech ka secure bridge. Yeh sirf data serve karne ka kaam karega (Read-only for frontend).  
> 3. **Data Acquisition Layer (Scraper Worker):** Background process jo scheduled time par e-pharmacies se prices nikal kar database mein push karega.

## **2\. Technology Stack**

| Component | Technology | Primary Reason |
| :---- | :---- | :---- |
| **Frontend Framework** | Next.js (App Router) | Server-Side Rendering (SSR) for maximum SEO benefits. |
| **Styling** | Tailwind CSS | Utility-first approach for rapid, consistent UI development. |
| **Backend API** | Python (FastAPI) | High performance, async support, and seamless integration with Python data tools. |
| **Scraping Engine** | Python (Playwright) | Ability to render complex JavaScript SPAs and bypass basic bot protections. |
| **Database** | PostgreSQL (Supabase) | Robust relational capabilities combined with scalable time-series data storage. |

## 

## **3\. Database Schema Design (PostgreSQL)**

Humein 4 core tables ki zaroorat hai. Supabase Row Level Security (RLS) use karke frontend ko sirf SELECT permission di jayegi.

### **Table 1: products (Master Catalog)**

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique identifier. |
| name | VARCHAR | NOT NULL | Product name (e.g., "Pan-D Capsule"). |
| slug | VARCHAR | UNIQUE | SEO-friendly URL slug. |
| composition | TEXT |  | Salt composition for fuzzy matching. |
| requires\_rx | BOOLEAN | DEFAULT FALSE | Flag for Schedule H drugs (Prescription required). |

### **Table 2: platforms (E-pharmacies)**

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | INT | PRIMARY KEY | Unique ID (e.g., 1 for 1mg, 2 for PharmEasy). |
| name | VARCHAR | UNIQUE | Platform name. |
| base\_url | VARCHAR | NOT NULL | Main website URL. |

### **Table 3: platform\_product\_links (Mapping)**

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique mapping ID. |
| product\_id | UUID | FOREIGN KEY | Links to products table. |
| platform\_id | INT | FOREIGN KEY | Links to platforms table. |
| scrape\_url | TEXT | NOT NULL | Target URL for the scraper. |
| affiliate\_tag | TEXT |  | Tracking tag for monetization. |

### 

### **Table 4: price\_history (Time-Series Data)**

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique record ID. |
| mapping\_id | UUID | FOREIGN KEY | Links to platform\_product\_links. |
| selling\_price | DECIMAL | NOT NULL | Final price after discount. |
| in\_stock | BOOLEAN | DEFAULT TRUE | Availability status. |
| scraped\_at | TIMESTAMP | DEFAULT NOW() | When the data was fetched. |

*(Indexing: price\_history table mein mapping\_id aur scraped\_at par Composite Index lagana zaroori hai fast chart rendering ke liye.)*

## **4\. Core API Endpoints (FastAPI)**

> 1. **GET /api/v1/search**  
   * **Params:** q (query string, e.g., "Pan D").  
   * **Response:** List of matching products (Name, Composition, Slug).  
   * **Logic:** Uses fuzzy text search on the products table.  
> 2. **GET /api/v1/products/{slug}/prices**  
   * **Response:** Today's best prices across all platforms.  
> 3. **GET /api/v1/products/{slug}/history**  
   * **Params:** days (default 30).  
   * **Response:** Time-series data points formatted for frontend charting libraries (Chart.js / Recharts).  
> 4. **GET /api/v1/redirect**  
   * **Params:** mapping\_id.  
   * **Logic:** Appends the affiliate tag to the base URL and returns a 302 Redirect to the merchant site.

## **5\. Scraper Engine Architecture**

Scraper ko Object-Oriented Programming (OOP) principles par design kiya jayega.

> * **BaseScraper Class:** Ek generic class jisme core scraping logic, rotating proxy setup, aur playwright-stealth configuration hogi.  
> * **Platform Specific Classes:** Tata1mgScraper, PharmEasyScraper jo BaseScraper ko inherit karengi aur apne specific DOM elements (XPath/CSS Selectors) define karengi.  
> * **Execution Flow:**  
  1. Cron job triggers at 2:00 AM IST.  
  2. Fetches active URLs from platform\_product\_links.  
  3. Iterates with randomized delays (e.g., 3.5s to 7.2s).  
  4. Bulk inserts new records into price\_history.

## 

## **6\. Security & Deployment**

> * **Database Security:** Supabase RLS policies will explicitly deny INSERT, UPDATE, DELETE operations from the public Anon key. Only the Service Role Key (used securely by the backend) can mutate data.  
> * **API Security:** FastAPI backend will implement slowapi for strict IP-based rate limiting (e.g., 60 req/min) to prevent competitor scraping. CORS will strictly allow only the production Next.js domain.  
> * **Deployment Target:**  
  * Frontend: Vercel  
  * API Backend: Render / Railway  
  * Scraper Worker: Isolated DigitalOcean Droplet / AWS EC2 (to maintain static/rotating IPs).