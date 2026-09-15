"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { ProductCard } from "@/components/ProductCard";
import { Search, Loader2, Stethoscope, Camera } from "lucide-react";
import LensSearchModal from "@/components/LensSearchModal";

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
  const [isLensOpen, setIsLensOpen] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Initial load — fetch popular medicines
  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);
      try {
        // Fetch products based on search or fetch all categories
        let endpoint = `${apiUrl}/products?limit=40`;
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

      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full py-[clamp(2rem,6vw,3rem)]">
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
            className="w-full pl-12 pr-14 py-3.5 rounded-full border-2 border-accent bg-white focus:border-primary focus:ring-0 text-base shadow-sm transition-colors outline-none"
            placeholder="Search medicines by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {isLoading && (
            <Loader2 className="absolute right-14 top-1/2 -translate-y-1/2 h-5 w-5 text-primary animate-spin" />
          )}
          <button
            type="button"
            onClick={() => setIsLensOpen(true)}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100 transition-colors"
            title="Search by Image"
          >
            <Camera className="w-5 h-5" />
          </button>
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
          <div className="space-y-12">
            {Object.entries(
              products.reduce((acc, product) => {
                const cat = product.category.charAt(0).toUpperCase() + product.category.slice(1);
                if (!acc[cat]) acc[cat] = [];
                acc[cat].push(product);
                return acc;
              }, {} as Record<string, Product[]>)
            ).map(([category, items]) => (
              <div key={category} className="space-y-4">
                <div className="flex items-center gap-2 border-b border-gray-100 pb-2">
                  <h2 className="text-xl font-bold text-gray-900">{category}</h2>
                  <span className="bg-gray-100 text-gray-500 text-xs font-bold px-2 py-0.5 rounded-full">
                    {items.length}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
                  {items.map((product) => (
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
              </div>
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
      <LensSearchModal isOpen={isLensOpen} onClose={() => setIsLensOpen(false)} />
    </main>
  );
}
