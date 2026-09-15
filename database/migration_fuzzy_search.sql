-- ============================================================
-- Migration: Fuzzy Search RPC + Missing Searches Improvements
-- Run this ONCE in your Supabase SQL Editor
-- ============================================================

-- 1. Ensure pg_trgm extension is enabled
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 2. Create missing_searches table (safe — skips if already exists)
CREATE TABLE IF NOT EXISTS public.missing_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query TEXT NOT NULL,
    search_type VARCHAR(20) DEFAULT 'text',
    status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Clean up duplicate search_query entries, then add unique constraint
--    Keeps the oldest row for each search_query, deletes newer duplicates.
DELETE FROM public.missing_searches a
USING public.missing_searches b
WHERE a.id > b.id
AND a.search_query = b.search_query;

CREATE UNIQUE INDEX IF NOT EXISTS idx_missing_searches_query_unique
ON public.missing_searches (search_query);

-- 4. Enable RLS + read policy (safe — idempotent)
ALTER TABLE public.missing_searches ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'missing_searches'
        AND policyname = 'Enable read access for all users'
    ) THEN
        CREATE POLICY "Enable read access for all users"
        ON public.missing_searches FOR SELECT USING (true);
    END IF;
END $$;

-- 5. Fuzzy search RPC function (pg_trgm similarity)
--    Takes an array of medicine names extracted from a prescription image.
--    Returns up to 3 fuzzy matches per name from the products table.
--    Unmatched names appear with NULL product columns (used to detect not_found).
--
--    Called from Python:
--      supabase.rpc("search_medicines_fuzzy", {"search_names": ["Paracetmol", "Azithromy"]})
CREATE OR REPLACE FUNCTION search_medicines_fuzzy(search_names text[])
RETURNS TABLE (
    search_term text,
    product_id uuid,
    product_name varchar(255),
    product_slug varchar(255),
    product_category varchar(50),
    product_image_url text,
    match_score real
)
LANGUAGE sql STABLE
AS $$
    SELECT
        s.term,
        p.id,
        p.name,
        p.slug,
        p.category,
        p.image_url,
        CASE WHEN p.id IS NOT NULL
             THEN similarity(p.name, s.term)
             ELSE NULL
        END
    FROM unnest(search_names) AS s(term)
    LEFT JOIN LATERAL (
        SELECT p2.id, p2.name, p2.slug, p2.category, p2.image_url
        FROM products p2
        WHERE similarity(p2.name, s.term) > 0.3
        ORDER BY similarity(p2.name, s.term) DESC
        LIMIT 3
    ) p ON true;
$$;
