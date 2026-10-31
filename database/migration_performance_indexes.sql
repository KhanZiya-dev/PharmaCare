-- ============================================================
-- Migration: Performance Indexes
-- Add missing indexes for common query patterns.
-- Run once in Supabase SQL Editor.
-- ============================================================

-- Slug lookups (used on every product/lab-test detail page)
CREATE INDEX IF NOT EXISTS idx_products_slug ON public.products (slug);
CREATE INDEX IF NOT EXISTS idx_lab_tests_slug ON public.lab_tests (slug);

-- Composition lookups (used for "alternatives" query)
CREATE INDEX IF NOT EXISTS idx_products_composition ON public.products (composition);

-- Foreign key lookups (used in joins — Postgres doesn't auto-index FK columns)
CREATE INDEX IF NOT EXISTS idx_platform_product_links_product_id ON public.platform_product_links (product_id);
CREATE INDEX IF NOT EXISTS idx_platform_lab_test_links_lab_test_id ON public.platform_lab_test_links (lab_test_id);

-- Price history mapping lookups (if not already covered by composite index)
CREATE INDEX IF NOT EXISTS idx_price_history_mapping_id ON public.price_history (mapping_id);
CREATE INDEX IF NOT EXISTS idx_lab_test_price_history_mapping_id ON public.lab_test_price_history (mapping_id);
