-- ============================================================
-- Migration: Smart Search RPC (Ranked Fuzzy + Composition)
-- Run this ONCE in your Supabase SQL Editor
-- ============================================================
-- Requires pg_trgm (already enabled via previous migration)

-- Smart search RPC: single DB call that returns ranked results
-- Supports: exact match, starts-with, fuzzy (pg_trgm), and composition match
-- Works for both medicines and lab tests via optional category_filter
--
-- Called from Python:
--   supabase.rpc("search_products_smart", {"query": "paracetmol"})
--   supabase.rpc("search_products_smart", {"query": "CBC", "category_filter": "diagnostic"})

CREATE OR REPLACE FUNCTION search_products_smart(
    query text,
    category_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    name varchar(255),
    slug varchar(255),
    category varchar(50),
    composition text,
    image_url text,
    match_type text,
    relevance real
)
LANGUAGE sql STABLE
AS $$
    WITH search_term AS (
        SELECT lower(trim(query)) AS q
    ),
    -- 1. Exact name match (case-insensitive)
    exact_matches AS (
        SELECT p.id, p.name, p.slug, p.category, p.composition, p.image_url,
               'exact'::text AS match_type,
               1.0::real AS relevance
        FROM products p, search_term s
        WHERE lower(p.name) = s.q
    ),
    -- 2. Starts-with match
    prefix_matches AS (
        SELECT p.id, p.name, p.slug, p.category, p.composition, p.image_url,
               'prefix'::text AS match_type,
               0.85::real AS relevance
        FROM products p, search_term s
        WHERE lower(p.name) LIKE (s.q || '%')
          AND lower(p.name) != s.q  -- exclude exact matches (already captured)
    ),
    -- 3. Fuzzy name match via pg_trgm similarity
    fuzzy_matches AS (
        SELECT p.id, p.name, p.slug, p.category, p.composition, p.image_url,
               'fuzzy'::text AS match_type,
               similarity(p.name, (SELECT q FROM search_term)) AS relevance
        FROM products p, search_term s
        WHERE similarity(p.name, s.q) > 0.25
          AND lower(p.name) != s.q
          AND NOT (lower(p.name) LIKE (s.q || '%'))
    ),
    -- 4. Composition match (find all brands with the searched salt/ingredient)
    composition_matches AS (
        SELECT p.id, p.name, p.slug, p.category, p.composition, p.image_url,
               'composition'::text AS match_type,
               0.5::real AS relevance
        FROM products p, search_term s
        WHERE p.composition IS NOT NULL
          AND lower(p.composition) LIKE ('%' || s.q || '%')
          AND lower(p.name) != s.q
          AND NOT (lower(p.name) LIKE (s.q || '%'))
          AND similarity(p.name, s.q) <= 0.25
    ),
    -- Combine all, deduplicate keeping highest relevance
    combined AS (
        SELECT DISTINCT ON (sub.id)
            sub.id, sub.name, sub.slug, sub.category, sub.composition,
            sub.image_url, sub.match_type, sub.relevance
        FROM (
            SELECT * FROM exact_matches
            UNION ALL
            SELECT * FROM prefix_matches
            UNION ALL
            SELECT * FROM fuzzy_matches
            UNION ALL
            SELECT * FROM composition_matches
        ) sub
        ORDER BY sub.id, sub.relevance DESC
    )
    SELECT c.id, c.name, c.slug, c.category, c.composition, c.image_url,
           c.match_type, c.relevance
    FROM combined c
    WHERE (category_filter IS NULL OR lower(c.category) = lower(category_filter))
    ORDER BY c.relevance DESC, c.name ASC
    LIMIT 12;
$$;
