-- Migration: Create dedicated lab_tests table

-- Table: lab_tests
CREATE TABLE public.lab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    sample_type VARCHAR(100), -- e.g., Blood, Urine
    fasting_required BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.lab_tests ENABLE ROW LEVEL SECURITY;

-- Read policy for anonymous users
CREATE POLICY "Enable read access for all users" ON public.lab_tests FOR SELECT USING (true);

-- GIN Index for fuzzy search on lab test names
CREATE INDEX idx_lab_tests_name_trgm ON public.lab_tests USING GIN (name gin_trgm_ops);

-- Note: To map prices to these tests, we might also need to update the platform_product_links 
-- table to reference lab_tests, or create a separate platform_lab_test_links table.

-- Table: platform_lab_test_links
CREATE TABLE public.platform_lab_test_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lab_test_id UUID REFERENCES public.lab_tests(id) ON DELETE CASCADE,
    platform_id INT REFERENCES public.platforms(id),
    scrape_url TEXT NOT NULL,
    affiliate_url TEXT,
    last_scraped TIMESTAMP
);

-- Table: lab_test_price_history
CREATE TABLE public.lab_test_price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mapping_id UUID REFERENCES public.platform_lab_test_links(id) ON DELETE CASCADE,
    mrp DECIMAL(10,2),
    selling_price DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2),
    in_stock BOOLEAN DEFAULT TRUE,
    is_restricted BOOLEAN DEFAULT FALSE,
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS and Read Policies for new tables
ALTER TABLE public.platform_lab_test_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_test_price_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON public.platform_lab_test_links FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON public.lab_test_price_history FOR SELECT USING (true);

-- Index for fast time-series fetching
CREATE INDEX idx_lab_test_price_history_mapping_time ON public.lab_test_price_history (mapping_id, scraped_at DESC);
