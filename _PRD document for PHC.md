# **Product Requirements Document (PRD)**

**Project Name:** PharmaCare (formerly HealthCompare) **Document Version:** 2.0 (MVP Finalized) **Platform Type:** Responsive Web Application (Mobile-First) **Primary Market:** India

## **1\. Product Objective**

Ek transparent aur user-friendly aggregator platform banana jahan log life-saving medicines aur diagnostic lab tests ka price alag-alag e-pharmacies (jaise 1mg, PharmEasy, Apollo) par real-time mein compare kar sakein. Platform ka USP **30-day Price History chart** hoga, jo users ko fake discounts se bachayega aur best purchasing decision lene mein madad karega.

## **2\. Target Audience**

> * **Chronic Patients:** Jinhe regular basis pe mehengi dawaiyan (BP, Diabetes, etc.) leni hoti hain.  
> * **Smart Shoppers:** Jo purchase se pehle historical price trends aur real discounts verify karna pasand karte hain.  
> * **Cost-Conscious Users:** Jo lab tests (e.g., Full Body Checkup, MRI) book karne se pehle prices compare karna chahte hain.

## **3\. Core Features (MVP Scope)**

### **A. Frontend & User Interface (Web)**

> 1. **High-Conversion Hero Section:**  
   * Clear, staggered animated text ("Smart Prices For Better Health").  
   * Floating interactive cards (showing sample medicine price drops aur trending deals).  
   * Trust-building visual anchors (verified data badges, premium healthcare imagery).  
> 2. **Smart Search System:**  
   * Fuzzy search support (spelling mistakes handle karne ke liye).  
   * Dropdown auto-suggestions with salt composition.  
> 3. **Product Detail Dashboard:**  
   * **Price Comparison Table:** Multiple platforms ke current prices, stock status, aur direct affiliate "Buy Now" links.  
   * **Price History Chart:** Line graph showing the last 30 days' price trends (highest, lowest, average).  
   * **Prescription Warning:** Schedule H drugs ke liye mandatory "Valid Prescription Required" badge.  
> 4. **Quick Support Integration:**  
   * Global sticky WhatsApp support button (with a generic/placeholder business number) for order assistance.

### 

### **B. Backend & Data Engine**

> 1. **Automated Web Scraper:**  
   * Python-based Playwright engine.  
   * Object-Oriented modular architecture (BaseScraper class jisse 1mg, PharmEasy, etc. inherit karenge).  
   * Anti-bot mechanisms: Rotating residential proxies, stealth plugins, aur randomized delays.  
   * Scheduled Cron Jobs jo raat ke non-peak hours mein chalenge.  
> 2. **Centralized Database:**  
   * Relational schema for products and platforms.  
   * Time-series storage for daily price history logs.  
> 3. **Secure API Layer:**  
   * FastAPI endpoints with strict CORS policies.  
   * Rate limiting to prevent competitor data scraping.

## **4\. User Flow**

> 1. **Landing:** User homepage par aata hai, clean UI aur trust badges dekhta hai.  
> 2. **Search:** Search bar mein dawai ya test ka naam enter karta hai.  
> 3. **Analyze:** Product page par aakar current prices aur 30-day history chart compare karta hai.  
> 4. **Action:** Sabse saste ya preferred platform ke "Track Price" / "Buy Now" button par click karta hai.  
> 5. **Routing:** Backend affiliate tag append karke user ko respective pharmacy ki website par redirect kar deta hai.

## **5\. Technology Stack**

| Component | Technology | Reason for Choice |
| :---- | :---- | :---- |
| **Frontend UI** | Next.js (React) \+ Tailwind CSS | SEO optimization, fast Server-Side Rendering, aur clean styling. |
| **Icons & Typography** | Lucide / Material Symbols, DM Serif & Inter | Premium, readable, and trustworthy medical aesthetics. |
| **Backend API** | Python (FastAPI) | Asynchronous support, extremely fast execution. |
| **Scraping Engine** | Python \+ Playwright | Handles dynamic JavaScript-heavy single-page applications. |
| **Database** | PostgreSQL (Supabase) | Handles both relational mapping and heavy time-series data; built-in Row Level Security (RLS). |

## 

## **6\. Security & Legal Compliance**

> * **Aggregator Disclaimer:** Har page par explicit text hoga stating that PharmaCare is an independent aggregator and does not sell or dispense medications directly.  
> * **Database Security:** Supabase Row Level Security (RLS) ensuring the frontend only has SELECT (Read) access, while INSERT/UPDATE is locked to the backend scraper.  
> * **Bot Protection:** Strict API rate limiting to block DDoS attempts or scraping of your database.

## **7\. Out of Scope (For Future Versions)**

> * User account creation and login systems.  
> * Automated email or WhatsApp "Price Drop Alerts".  
> * Direct payment gateway integration or in-house fulfillment.