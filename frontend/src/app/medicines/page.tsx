"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { ProductCard } from "@/components/ProductCard";
import { Search, Loader2, Stethoscope } from "lucide-react";

interface Product {
  id: string;
  name: string;
  slug: string;
  category: string;
  composition?: string;
  image_url?: string;
}

export default function MedicinesPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Initial load — fetch popular medicines
  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);
      try {
        // Fetch products based on search or category default
        let endpoint = `${apiUrl}/products?category=medicine`;
        if (searchQuery.trim().length >= 2) {
          endpoint = `${apiUrl}/search?q=${encodeURIComponent(searchQuery)}`;
        }
        const res = await fetch(endpoint);
        if (res.ok) {
          const data = await res.json();
          setProducts(data);
        }
      } catch (error) {
        console.error("Error fetching medicines:", error);
      } finally {
        setIsLoading(false);
      }
    }

    const timer = setTimeout(fetchProducts, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, apiUrl]);

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-10">
        {/* Page Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="bg-blue-50 p-2.5 rounded-xl">
              <Stethoscope className="h-6 w-6 text-primary" />
            </div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold text-primary">
              Browse Medicines
            </h1>
          </div>
          <p className="text-gray-500 max-w-2xl">
            Search and compare prices for life-saving medicines across top Indian e-pharmacies. Track prices and never overpay.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-xl mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            className="w-full pl-12 pr-4 py-3.5 rounded-full border-2 border-accent bg-white focus:border-primary focus:ring-0 text-base shadow-sm transition-colors outline-none"
            placeholder="Search medicines by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {isLoading && (
            <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary animate-spin" />
          )}
        </div>

        {/* Product Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-accent overflow-hidden">
                <div className="skeleton h-40 w-full rounded-none" />
                <div className="p-4 space-y-2">
                  <div className="skeleton h-4 w-16 rounded-full" />
                  <div className="skeleton h-5 w-3/4" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                name={product.name}
                slug={product.slug}
                category={product.category}
                composition={product.composition}
                image_url={product.image_url}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="bg-gray-50 inline-block p-4 rounded-full mb-4">
              <Search className="h-8 w-8 text-gray-300" />
            </div>
            <h3 className="font-bold text-foreground text-lg mb-1">No medicines found</h3>
            <p className="text-gray-500 text-sm">Try a different search term or check the spelling.</p>
          </div>
        )}
      </div>
    </main>
  );
}
