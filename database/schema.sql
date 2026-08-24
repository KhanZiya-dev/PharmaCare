-- Enable extensions for UUID and Fuzzy Search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Table 1: products (The Master Catalog)
CREATE TABLE public.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    composition TEXT,
    requires_rx BOOLEAN DEFAULT FALSE,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: platforms (The E-Pharmacies)
CREATE TABLE public.platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    logo_url TEXT
);

-- Table 3: platform_product_links (The Mapping Engine)
CREATE TABLE public.platform_product_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES public.products(id) ON DELETE CASCADE,
    platform_id INT REFERENCES public.platforms(id),
    scrape_url TEXT NOT NULL,
    affiliate_url TEXT,
    last_scraped TIMESTAMP
);

-- Table 4: price_history (Time-Series Log)
CREATE TABLE public.price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mapping_id UUID REFERENCES public.platform_product_links(id) ON DELETE CASCADE,
    mrp DECIMAL(10,2),
    selling_price DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2),
    in_stock BOOLEAN DEFAULT TRUE,
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Speed Optimization
-- GIN Index for typo-tolerant (fuzzy) search
CREATE INDEX idx_products_name_trgm ON public.products USING GIN (name gin_trgm_ops);
CREATE INDEX idx_products_composition_trgm ON public.products USING GIN (composition gin_trgm_ops);

-- Composite B-Tree Index for Time-Series Fetching
CREATE INDEX idx_price_history_mapping_time ON public.price_history (mapping_id, scraped_at DESC);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_product_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_history ENABLE ROW LEVEL SECURITY;

-- 1. Frontend (Anon Key) - Read Only
CREATE POLICY "Enable read access for all users" ON public.products FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON public.platforms FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON public.platform_product_links FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON public.price_history FOR SELECT USING (true);

-- Note: The Service Role Key (used by backend/scraper) automatically bypasses RLS,
-- so we do not need to create explicit INSERT/UPDATE/DELETE policies for the scraper API.
