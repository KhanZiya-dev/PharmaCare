-- ============================================================
-- Migration: Trends Variance RPC (Performance Optimization)
-- Moves heavy nested-join + Python computation into a single
-- efficient SQL query. Run once in Supabase SQL Editor.
-- ============================================================

CREATE OR REPLACE FUNCTION get_high_variance_products(result_limit int DEFAULT 12)
RETURNS TABLE (
    id uuid,
    name varchar(255),
    slug varchar(255),
    category varchar(50),
    image_url text,
    lowest_price numeric,
    highest_price numeric,
    variance_pct numeric,
    discount_pct numeric,
    platform_count bigint
)
LANGUAGE sql STABLE
AS $$
    WITH latest_prices AS (
        -- Get the most recent price per mapping (using the existing index on mapping_id, scraped_at DESC)
        SELECT DISTINCT ON (ph.mapping_id)
            ph.mapping_id,
            ph.selling_price,
            ph.mrp,
            ph.in_stock,
            ph.is_restricted
        FROM price_history ph
        ORDER BY ph.mapping_id, ph.scraped_at DESC
    ),
    product_prices AS (
        -- Join to get product info + all latest prices per product
        SELECT
            p.id,
            p.name,
            p.slug,
            p.category,
            p.image_url,
            lp.selling_price
        FROM products p
        JOIN platform_product_links ppl ON ppl.product_id = p.id
        JOIN latest_prices lp ON lp.mapping_id = ppl.id
        WHERE lp.selling_price > 0
          AND lp.in_stock IS NOT FALSE
          AND (lp.is_restricted IS NULL OR lp.is_restricted = false)
    ),
    aggregated AS (
        SELECT
            pp.id,
            pp.name,
            pp.slug,
            pp.category,
            pp.image_url,
            MIN(pp.selling_price) AS min_price,
            MAX(pp.selling_price) AS max_price,
            COUNT(*) AS platform_count
        FROM product_prices pp
        GROUP BY pp.id, pp.name, pp.slug, pp.category, pp.image_url
        HAVING COUNT(*) > 1               -- need at least 2 platforms for variance
           AND MIN(pp.selling_price) >= 10  -- filter glitch data
           AND MAX(pp.selling_price) <= 50000
    )
    SELECT
        a.id,
        a.name,
        a.slug,
        a.category,
        a.image_url,
        a.min_price AS lowest_price,
        a.max_price AS highest_price,
        ROUND(((a.max_price - a.min_price) / a.min_price) * 100, 2) AS variance_pct,
        ROUND(((a.max_price - a.min_price) / a.max_price) * 100, 2) AS discount_pct,
        a.platform_count
    FROM aggregated a
    WHERE ((a.max_price - a.min_price) / a.min_price) * 100 <= 85  -- filter suspicious data
      AND ((a.max_price - a.min_price) / a.min_price) * 100 > 0
    ORDER BY variance_pct DESC
    LIMIT result_limit;
$$;
