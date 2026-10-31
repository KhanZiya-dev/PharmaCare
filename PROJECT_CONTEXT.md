# 🧠 PharmaCare — Project Context & Memory File

> **PURPOSE:** Ye file project ka complete "brain" hai. Jab bhi naya model, naya conversation, ya naya agent start ho — pehle ye file padho. Isse poora project samajh aa jayega bina codebase explore kiye.
>
> **RULE FOR AI:** Jab bhi quota khatam hone wala ho ya conversation end ho raha ho, **is file ko update karo** latest progress, bugs, decisions, aur pending tasks ke saath. Ye file hamesha up-to-date rehni chahiye.

---

## 📅 Last Updated
- **Date:** 2026-10-31 (14:57 IST)
- **Updated By:** Gemini 3.8 Flash
- **Conversation Summary:** Fixed 1mg "Data unavailable" issue (staleness-based scraper priority queue + latest_price without time limit + 30/90 day chart toggle). Fixed PriceHistoryChart dark mode visibility issues (high-contrast line/legend colors, dark custom tooltip, theme-aware axis/grid, hollow dot rings).

---

## 🏗️ Project Overview

**PharmaCare** ek medicine & lab test **price comparison aggregator** hai — India ke liye.

### What It Does:
- Multiple e-pharmacies (1mg, PharmEasy, Apollo, Zeno Health) se **real-time prices scrape** karta hai
- Users ko ek **30-day price history chart** dikhata hai taaki fake discounts pakde ja sakein
- **Lab tests** (blood tests, full body checkups) ke prices bhi compare karta hai (Metropolis, Thyrocare, Lal Pathlabs, Agilus)
- **Vision Search:** User prescription ki photo upload kare → Gemini AI se medicine names extract hoti hain → DB se match hoke results aate hain
- **Generic Alternatives:** Zeno Health API se cheaper generic substitutes bhi dikhata hai

### USP (Unique Selling Point):
> "Don't fall for fake discounts — check our 30-day price history before you buy."

---

## 🛠️ Tech Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Frontend** | Next.js 16.3.1 + React 19 | App Router, Tailwind CSS v4, TypeScript |
| **Backend API** | FastAPI (Python 3.12) | Uvicorn server, async endpoints |
| **Scraper** | Playwright + Stealth | Headless Chromium, anti-bot measures |
| **Database** | PostgreSQL (Supabase) | pg_trgm for fuzzy search, RLS enabled |
| **AI/Vision** | Google Gemini 3.6 Flash | Prescription image OCR |
| **Live Pricing** | Zeno Health API | Real-time API (no scraping needed) |
| **Hosting** | Render (Backend) + Vercel (Frontend) | |
| **Cron** | cron-job.org (external) | Hits `/cron/update-prices` endpoint |

---

## 📁 Project Structure

```
Pharmacare/
├── frontend/                    # Next.js 16 App
│   └── src/
│       ├── app/
│       │   ├── page.tsx                # Homepage (hero + search + panels)
│       │   ├── layout.tsx              # Root layout (Navbar, Footer, ThemeProvider)
│       │   ├── globals.css             # Tailwind + custom styles
│       │   ├── product/[slug]/page.tsx  # Medicine detail (prices, chart, alternatives)
│       │   ├── lab-tests/[slug]/page.tsx # Lab test detail page
│       │   ├── lab-tests/page.tsx       # Lab tests listing
│       │   ├── medicines/page.tsx       # Medicines listing
│       │   └── trends/page.tsx          # Price variance / trending deals
│       ├── components/
│       │   ├── Navbar.tsx              # Top navigation bar
│       │   ├── Footer.tsx              # Site footer
│       │   ├── SearchAutocomplete.tsx  # Smart search with dropdown
│       │   ├── LensSearchModal.tsx     # Camera/prescription upload modal
│       │   ├── PriceHistoryChart.tsx   # Recharts line chart (30-day)
│       │   ├── ComparisonTable.tsx     # Platform price comparison table
│       │   ├── ProductCard.tsx         # Medicine/test card component
│       │   ├── FloatingCards.tsx       # Hero section animated cards
│       │   ├── ScannerCTA.tsx          # "Scan Prescription" CTA panel
│       │   ├── StickyHeroSearch.tsx    # Sticky search on scroll
│       │   ├── ThemeProvider.tsx       # Dark/Light theme (next-themes)
│       │   ├── ThemeToggle.tsx         # Theme switcher button
│       │   ├── ShareButton.tsx         # Share product link
│       │   ├── BackButton.tsx          # Navigation back button
│       │   └── MobileTabBar.tsx        # Bottom tab bar for mobile
│       └── utils/
│           └── urlParser.ts            # URL utility functions
│
├── backend/                     # FastAPI Backend
│   ├── main.py                  # API server (all endpoints)
│   ├── vision.py                # Gemini AI prescription OCR
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Secrets (Supabase + Gemini keys)
│   ├── scraper/
│   │   ├── base_scraper.py      # Abstract base (JSON-LD, text extraction, stock/restricted detection)
│   │   ├── engine.py            # Scraper orchestrator (anti-block, parallel workers)
│   │   ├── onemg_scraper.py     # 1mg specific scraper
│   │   ├── pharmeasy_scraper.py # PharmEasy specific scraper
│   │   ├── apollo_scraper.py    # Apollo Pharmacy scraper
│   │   ├── lab_test_scraper.py  # Generic lab test scraper (Metropolis, Thyrocare, etc.)
│   │   ├── zeno.py              # Zeno Health API client (no scraping)
│   │   ├── scheduler.py         # (Deprecated — now using external cron)
│   │   └── __init__.py
│   ├── scripts/                 # One-off DB/data maintenance scripts
│   └── scratch/                 # Debug/test scripts
│
├── render.yaml                  # Render.com deployment config
├── .env                         # Root env (same as backend/.env)
└── [docs]                       # PRD, TRD, UI/UX docs, schema docs
```

---

## 🗃️ Database Schema (Supabase PostgreSQL)

### Core Tables:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────┐     ┌────────────────┐
│  products   │────▶│ platform_    │────▶│    price_history     │     │   platforms    │
│             │     │ product_links│     │                      │     │                │
│ id (UUID)   │     │ id (UUID)    │     │ id (UUID)            │     │ id (SERIAL)    │
│ name        │     │ product_id   │     │ mapping_id (FK)      │     │ name           │
│ slug        │     │ platform_id  │     │ mrp                  │     │ base_url       │
│ category    │     │ scrape_url   │     │ selling_price        │     │ logo_url       │
│ composition │     │ affiliate_url│     │ discount_pct         │     └────────────────┘
│ requires_rx │     │ last_scraped │     │ in_stock             │
│ image_url   │     └──────────────┘     │ is_restricted        │
└─────────────┘                          │ scraped_at           │
                                         └──────────────────────┘

┌─────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│  lab_tests  │────▶│ platform_lab_test_    │────▶│ lab_test_price_history   │
│             │     │ links                 │     │                          │
│ id (UUID)   │     │ id (UUID)             │     │ id, mapping_id, mrp,     │
│ name        │     │ lab_test_id           │     │ selling_price, in_stock, │
│ slug        │     │ platform_id           │     │ scraped_at               │
│ description │     │ scrape_url            │     └──────────────────────────┘
│ sample_type │     │ affiliate_url         │
└─────────────┘     └──────────────────────┘

┌───────────────────┐
│ missing_searches  │  ← Logs searches with zero results (disabled currently)
│ search_query      │
│ search_type       │
└───────────────────┘
```

### Key DB Features:
- **pg_trgm** extension for fuzzy/typo-tolerant search
- **RPC Functions:**
  - `search_products_smart` — ranked product search
  - `search_medicines_fuzzy` — vision search matching (pg_trgm similarity)
  - `get_high_variance_products` — trending price drops (DB-side computation)
- **RLS Policies:** Anon key = SELECT only; Service role = full access
- **Indexes:** GIN on name/composition, B-Tree composite on (mapping_id, scraped_at)

---

## 🔌 API Endpoints (FastAPI — `backend/main.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| GET | `/search?q=...&category=...&type=...` | Smart product search (5-min cache) |
| GET | `/products?category=...&type=...&limit=40` | Product listing (10-min cache) |
| GET | `/product/{slug}?days=30` | Full product detail + prices + history + Zeno live + alternatives (days: 7-90) |
| GET | `/lab-tests?limit=40` | Lab test listing |
| GET | `/lab-test/{slug}?days=30` | Lab test detail + prices + history (days: 7-90) |
| GET | `/trends/variance` | High price variance products (30-min cache) |
| GET | `/redirect?mapping_id=...` | Affiliate redirect (HTTP 307) |
| POST | `/api/vision-search` | Upload prescription image → extract medicine names → match products |
| GET | `/cron/update-prices` | Trigger scraper (background task) |

### Caching Strategy:
- In-memory TTL cache (dict-based, no Redis)
- Search: 5 min, Products list: 10 min, Product detail: 5 min, Zeno live: 15 min, Trends: 30 min
- Auto-eviction when cache > 2000 entries

### Rate Limiting:
- SlowAPI: 60/min on most endpoints, 20/min on vision search

---

## 🕷️ Scraper Architecture

### How It Works:
1. External cron (cron-job.org) hits `GET /cron/update-prices`
2. `engine.py` fetches all `platform_product_links` + `platform_lab_test_links` from Supabase
3. Links are grouped by platform (1mg, PharmEasy, Apollo, Other)
4. **One dedicated async worker per platform** — processes URLs **sequentially** (anti-block)
5. All platform workers run **in parallel** via `asyncio.gather()`
6. Each worker rotates browser context every 50 requests
7. Failed URLs get one retry with longer cooldown

### Anti-Bot Measures:
- `playwright-stealth` plugin
- `fake-useragent` for random User-Agents
- Random delays: 5-8s normal, 15-30s retry, 45s block cooldown
- Browser context rotation every 50 requests
- CAPTCHA/block detection (checks page title, body length, CF challenge)

### Data Extraction Pipeline (per URL):
1. `extract_data()` — platform-specific selectors (override in subclass)
2. `_extract_json_ld()` — schema.org Product/Drug structured data
3. `_extract_next_data()` — Next.js __NEXT_DATA__ (for Apollo)
4. `_extract_prices_from_text()` — regex fallback on visible text
5. `_check_restricted_status()` — "Not for Online Sale" detection (scoped to product area, excludes footer/FAQ)
6. `_check_stock_status()` — multi-signal OOS detection (CSS classes, text badges, buttons)
7. Post-validation: price sanity checks, selling > MRP swap, suspicious price filtering

### Platform Scrapers:
| Scraper Class | Platform | File |
|--------------|----------|------|
| `OneMgScraper` | Tata 1mg | `onemg_scraper.py` |
| `PharmEasyScraper` | PharmEasy | `pharmeasy_scraper.py` |
| `ApolloScraper` | Apollo Pharmacy | `apollo_scraper.py` |
| `GenericLabTestScraper` | Metropolis, Thyrocare, Lal Pathlabs, Agilus | `lab_test_scraper.py` |
| `fetch_zeno_price()` | Zeno Health | `zeno.py` (API, no scraping) |

### Zeno Health (Special):
- Uses **public API** directly (no Playwright needed)
- Called **live on every product detail page** (cached 15 min)
- Also provides **generic alternatives** (cheaper drugs with same composition)
- Prices are persisted to `price_history` in background for historical tracking

---

## 👁️ Vision Search (Prescription OCR)

### Flow:
1. User uploads prescription photo via `LensSearchModal.tsx`
2. Frontend POSTs to `/api/vision-search`
3. Backend saves temp file, resizes to 800×800 max
4. Calls **Gemini 3.6 Flash** with structured prompt
5. Gemini returns JSON array of medicine names
6. Backend fuzzy-matches names against DB using `search_medicines_fuzzy` RPC (pg_trgm)
7. Falls back to ilike if RPC unavailable
8. Returns matched products + extracted text + not-found names

### Key Details:
- Model: `gemini-3.6-flash`
- Multiple API keys (comma-separated in env) for rotation/failover
- 10MB max upload, JPEG/PNG/WebP only
- 170s timeout guard (to prevent 180s frontend timeout)
- Rate limit: 20/min

---

## 🎨 Frontend Architecture

### Framework: Next.js 16 (App Router)
- **Server Components** by default (SSR)
- **Client Components** where interactivity needed (search, modals, charts, theme toggle)
- **ISR:** trends page revalidates every 3600s

### Key UI Libraries:
- **Tailwind CSS v4** (via `@tailwindcss/postcss`)
- **Recharts** — price history line charts
- **Framer Motion** — animations
- **Lucide React** — icons
- **Sonner** — toast notifications
- **next-themes** — dark/light mode
- **nextjs-toploader** — teal loading bar

### Design System:
- Fonts: Inter (body) + DM Serif Display (headings)
- Primary color: Teal (#00796B)
- Mobile-first responsive (clamp-based sizing)
- Dark mode supported

### Key Pages:
| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `page.tsx` | Hero + search + 3 panels (price drops, scanner CTA, stats) |
| `/product/[slug]` | `product/[slug]/page.tsx` | Full product view (comparison table, chart, alternatives, generics) |
| `/lab-tests` | `lab-tests/page.tsx` | Lab test listing |
| `/lab-tests/[slug]` | `lab-tests/[slug]/page.tsx` | Lab test detail |
| `/medicines` | `medicines/page.tsx` | Medicines listing |
| `/trends` | `trends/page.tsx` | Price variance / trending deals |

### Environment Variables (Frontend):
- `NEXT_PUBLIC_API_URL` — backend URL (default: `http://localhost:8000`)

---

## 🚀 Deployment

### Backend (Render):
- **Service:** Web service, Python environment
- **Build:** `cd backend && pip install -r requirements.txt && playwright install chromium`
- **Start:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance:** 0.1 CPU (free/starter tier)
- **Env vars:** SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GEMINI_API_KEY

### Frontend (Vercel):
- **URL:** `https://pharma-care-alpha.vercel.app`
- **Domain:** `https://pharmacare.in` (production)

### Cron:
- **Service:** cron-job.org (external, free)
- **Job:** Hits `GET /cron/update-prices` on schedule
- **Why external:** Saves ~5-10% CPU on the 0.1 CPU Render instance

---

## 🔐 Security

- **CORS:** Currently open (`allow_origins=["*"]`) — tighten for production
- **RLS:** Supabase Row Level Security enabled
- **Rate Limiting:** SlowAPI (per-IP)
- **Input Validation:** File type/size checks on vision upload
- **Service Role Key:** Used only server-side, never exposed to frontend
- **Temp Files:** Cleaned up in `finally` block after vision processing

---

## 📊 Current State & Progress

### ✅ Completed:
- Full scraper system (1mg, PharmEasy, Apollo, Zeno, lab test platforms)
- All API endpoints working
- Frontend all pages (home, product detail, lab test detail, medicines, trends)
- Vision/prescription search with Gemini
- Price history charts
- Generic alternatives display
- Dark/light theme
- Mobile responsive design
- Affiliate redirect system
- Render + Vercel deployment
- External cron setup

### 🔧 Known Issues / Improvements Needed:
- CORS is open (`*`) — should restrict to known origins in production
- `missing_searches` logging is disabled (to save DB space during testing)
- Some scraper false positives for "restricted" status (e.g. FAQ text triggering it)
- Render free tier is slow (0.1 CPU) — cold starts are painful

### 📝 Pending / Future Ideas:
- Price alerts / notifications
- User accounts / favorites
- PWA support
- More platforms (Netmeds, etc.)
- Real affiliate partnerships
- SEO optimization (meta tags, sitemaps done)
- College project report ("Black Book") — see `PROJECT_REPORT_INSTRUCTIONS.md`

---

## 🔑 Environment Variables Reference

### Backend (`backend/.env`):
```
SUPABASE_URL=https://vigdsauejhcurwcoydvy.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<jwt-token>
GEMINI_API_KEY=<key1>,<key2>,<key3>   # Comma-separated for rotation
```

### Frontend:
```
NEXT_PUBLIC_API_URL=http://localhost:8000   # or production backend URL
```

---

## 💡 Important Patterns & Conventions

1. **Caching:** All caching is in-memory dict with TTL. No Redis.
2. **Slug-based routing:** Products/tests use URL slugs, not IDs.
3. **Dual table system:** Products + Lab tests have separate but mirror tables (products ↔ lab_tests, platform_product_links ↔ platform_lab_test_links, price_history ↔ lab_test_price_history).
4. **Scraper is NOT scheduled internally** — external cron triggers it via HTTP.
5. **Zeno is API-based**, all others are Playwright scrapers.
6. **Vision search** uses multiple Gemini API keys with failover.
7. **Frontend uses `NEXT_PUBLIC_API_URL`** env var to find the backend.
8. **Category system:** `medicine` or `lab_test` (stored in products.category).

---

## 🗒️ Session Notes (Latest First)

### 2026-10-31 — Context File Creation
- Created this PROJECT_CONTEXT.md file
- Purpose: Any new AI model/conversation can read this and understand the entire project instantly
- **Action for future AI:** Always update the "Session Notes" section and "Last Updated" date before ending a conversation

---

> **⚠️ IMPORTANT FOR AI MODELS:**
> 1. **START** every new conversation by reading this file
> 2. **END** every conversation by updating this file with what was done, what changed, and what's pending
> 3. Update the "Last Updated" section with the current date and a brief summary
> 4. Add a new entry under "Session Notes" with details of the conversation
> 5. If any code architecture changed significantly, update the relevant sections above

