# **PharmaCare: 6-Week Implementation Plan (MVP)**

**Project Goal:** Launch a fully functional web aggregator with live scraping, search, and price history tracking for top medicines and lab tests. **Methodology:** Agile Sprints (1 Week \= 1 Sprint)

## **Phase 1: Foundation & Database Lock (Week 1\)**

**Goal:** Core infrastructure setup aur Supabase schema live karna.

> * **DevOps Setup:** GitHub repository initialize karo (Frontend aur Backend ke liye alag folders).  
> * **Database (Supabase):** \* Dashboard par naya project banao.  
  * TRD ke hisaab se 4 tables (products, platforms, platform\_product\_links, price\_history) create karne ke liye SQL script run karo.  
  * **Security:** Row Level Security (RLS) policies set karo taaki public access sirf "Read-Only" rahe.  
> * **Initial Seeding:** Top 100 fast-moving medicines (jaise BP, Diabetes) aur 10 common lab tests ka data products table mein manually ya CSV se upload karo.

## **Phase 2: The Scraper Engine (Week 2 & 3\)**

**Goal:** E-pharmacies se data lane wala robust engine taiyaar karna. Isme sabse zyada time lagega kyunki anti-bot bypass karna tricky hota hai.

> * **Week 2 (Core Logic):**  
  * Python mein OOP based BaseScraper class likho jisme Playwright aur playwright-stealth integrated ho.  
  * Specific platforms (1mg, PharmEasy, Apollo) ke liye child classes bana kar unke CSS selectors/XPaths configure karo.  
> * **Week 3 (Automation & Mapping):**  
  * Database ki platform\_product\_links table se URLs fetch karke scraper ko feed karne ka logic likho.  
  * Scraped data (selling price, MRP, stock) ko price\_history table mein push karne ka script final karo.  
  * Rotating residential proxies test karo taaki IP block na ho.

## **Phase 3: API Layer & Frontend Connect (Week 4\)**

**Goal:** Backend ko frontend se baat karne ke layaq banana.

> * **FastAPI Setup:** Python backend initialize karo aur Supabase client connect karo.  
> * **Core Endpoints Development:**  
  * GET /search: Fuzzy search implement karo.  
  * GET /product/{slug}: Current prices aur 30-day history data fetch karne ka endpoint.  
  * GET /redirect: Affiliate tags append karke platform par redirect karne wala route.  
> * **Security:** APIs par rate-limiting (slowapi) aur strict CORS policy lagao.

## **Phase 4: Frontend Development & UI Polish (Week 5\)**

**Goal:** User experience (UXDD) ko Next.js / React mein code karna.

> * **UI Components:** Tailwind CSS use karke Navbar, Floating Hero Cards, aur Product Table components design karo.  
> * **Integration:**  
  * Search bar ko FastAPI ke /search endpoint se jodo.  
  * Product page par Chart.js ya Recharts library use karke price history graph render karo.  
> * **Support Channel:** Global sticky "WhatsApp Support" button integrate karo (generic business link ke saath).

## **Phase 5: Testing, Cron Jobs & Launch (Week 6\)**

**Goal:** System ko live environment mein daalna aur bugs fix karna.

> * **Automation (Cron Job):** Scraper script ko DigitalOcean Droplet ya AWS EC2 par deploy karo aur Linux Cron ya schedule library se raat 2:00 AM ka trigger set karo.  
> * **QA & Testing:**  
  * Mobile layout check karo (responsive testing).  
  * Verify karo ki history chart sahi se render ho raha hai aur prices accurately update ho rahe hain.  
> * **Deployment:**  
  * Frontend ko Vercel par deploy karo.  
  * FastAPI backend ko Render ya Railway par live karo.  
  * Domain DNS (pharmacare.in ya jo bhi domain ho) configure karo.

**Milestone Checklist for Go-Live:**

> * \[ \] Supabase RLS is active (No unauthorized writes).  
> * \[ \] Scraper successfully runs automatically for 3 consecutive days without IP bans.  
> * \[ \] Search responds in under 300ms.  
> * \[ \] Affiliate redirection tracks clicks properly.