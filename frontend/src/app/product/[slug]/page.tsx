import { ComparisonTable } from "@/components/ComparisonTable";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { SearchAutocomplete } from "@/components/SearchAutocomplete";
import { ProductCard } from "@/components/ProductCard";
import { ScannedMedicinesNav } from "@/components/ScannedMedicinesNav";
import { AlertCircle, ChevronLeft, Pill, Replace } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ProductImage } from "./ProductImage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getProductData(slug: string) {
  try {
    const res = await fetch(`${API_URL}/product/${slug}`, {
      next: { revalidate: 60 }
    });
    
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error('Failed to fetch product');
    }
    
    return res.json();
  } catch (error) {
    console.error("Error fetching product:", error);
    return null;
  }
}

// Dynamic SEO metadata per product
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const data = await getProductData(slug);

  if (!data) {
    return {
      title: "Product Not Found — PharmaCare",
    };
  }

  const { product } = data;
  return {
    title: `${product.name} — Compare Prices | PharmaCare`,
    description: `Compare prices for ${product.name}${product.composition ? ` (${product.composition})` : ""} across top Indian e-pharmacies. View 30-day price history and find the best deal.`,
  };
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const data = await getProductData(slug);

  if (!data) {
    notFound();
  }

  const { product, platforms, alternatives, generics } = data;

  const activePlatforms = platforms.filter((p: any) => p.latest_price?.selling_price > 0 && !(p.latest_price as any)?.is_restricted);
  const prices = activePlatforms.map((p: any) => p.latest_price.selling_price);
  const lowestPrice = prices.length > 0 ? Math.min(...prices) : null;
  const highestPrice = prices.length > 0 ? Math.max(...prices) : null;
  const savingsPct = lowestPrice && highestPrice && highestPrice > lowestPrice 
    ? Math.round(((highestPrice - lowestPrice) / highestPrice) * 100) 
    : 0;

  return (
    <main className="min-h-screen bg-gray-50/50 flex flex-col">

      <div className="flex-1 max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full py-[clamp(1.5rem,5vw,3rem)]">
        
        {/* Top Navigation & Search */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <Link href="/" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-primary transition-colors">
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Search
          </Link>
          <div className="w-full md:w-96 page-search-bar transition-opacity duration-500">
            <SearchAutocomplete />
          </div>
        </div>

        {/* Scanned Medicines Quick Nav */}
        <ScannedMedicinesNav />

        {/* Product Header - Dashboard Style */}
        <div className="bg-white rounded-2xl p-5 md:p-6 shadow-sm border border-accent mb-8 flex flex-col md:flex-row gap-6 items-start md:items-center">
          <div className="shrink-0 w-24 h-24 bg-gray-50 rounded-xl flex items-center justify-center p-2 border border-gray-100 hidden md:flex">
            <ProductImage imageUrl={product.image_url} name={product.name} />
          </div>
          
          <div className="flex-1 min-w-0 w-full">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h1 className="font-serif text-2xl md:text-3xl font-bold text-gray-900 truncate">
                {product.name}
              </h1>
              {product.requires_rx && (
                <span className="inline-flex items-center gap-1 bg-red-50 text-red-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-200 uppercase tracking-wider">
                  <AlertCircle className="h-3 w-3" />
                  Rx Required
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2 mb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md">
                {product.category}
              </span>
              {product.composition && (
                <span className="text-xs text-gray-500 truncate border-l border-gray-200 pl-2">
                  {product.composition}
                </span>
              )}
            </div>
            
            {/* Quick Metrics Bar */}
            <div className="flex flex-wrap gap-3 sm:gap-6 pt-4 border-t border-gray-100">
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Tracked Platforms</p>
                <p className="text-[clamp(1.5rem,4vw,2.5rem)] font-black text-gray-900">{platforms.length}</p>
              </div>
              
              <div className="border-l border-gray-100 pl-3 sm:pl-6">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Current Lowest</p>
                <p className="text-[clamp(1.5rem,4vw,2.5rem)] font-black text-green-600">
                  {lowestPrice ? `₹${lowestPrice}` : "N/A"}
                </p>
              </div>
              
              {savingsPct > 0 && (
                <div className="border-l border-gray-100 pl-3 sm:pl-6">
                  <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Max Savings</p>
                  <p className="text-lg font-bold text-primary">
                    {savingsPct}%
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Comparison Table */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h2 className="font-bold text-2xl text-foreground mb-4">Compare Prices</h2>
              <ComparisonTable platforms={platforms} />
            </div>
            
            <div className="bg-blue-50/50 rounded-xl p-4 border border-blue-100 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-900">
                <strong>Disclaimer:</strong> PharmaCare is an independent aggregator. We do not sell medications directly. Prices are fetched directly from partner pharmacies and may change based on your location and their stock availability.
              </p>
            </div>
          </div>

          {/* Right Column: Price History Chart */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <PriceHistoryChart platforms={platforms} />
            </div>
          </div>

        </div>

        {/* Zeno Health Generic Alternatives Section */}
        {generics && generics.length > 0 && (
          <div className="mt-12 mb-8 bg-green-50/50 rounded-2xl p-6 border border-green-100">
            <div className="flex items-center gap-2 mb-6">
              <div className="bg-green-100 p-2 rounded-lg">
                <Replace className="h-6 w-6 text-green-700" />
              </div>
              <div>
                <h2 className="font-bold text-2xl text-green-900">
                  Save More with Generics
                </h2>
                <p className="text-sm text-green-700 mt-1">Cheaper generic substitutes found by Zeno Health</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {generics.map((alt: any, idx: number) => {
                const discount = alt.mrp && alt.price ? Math.round(((alt.mrp - alt.price) / alt.mrp) * 100) : 0;
                return (
                  <div key={idx} className="bg-white rounded-xl p-4 border border-green-200 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-gray-900 line-clamp-2">{alt.name}</h3>
                        {discount > 0 && (
                          <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded">
                            {discount}% OFF
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mb-3">{alt.company}</p>
                      <p className="text-xs text-gray-400 bg-gray-50 p-2 rounded truncate">{alt.pack}</p>
                    </div>
                    <div className="mt-4 flex items-end justify-between pt-3 border-t border-gray-100">
                      <div>
                        {alt.mrp && (
                          <p className="text-xs text-gray-400 line-through">₹{alt.mrp}</p>
                        )}
                        <p className="text-lg font-black text-green-600">₹{alt.price}</p>
                      </div>
                      <a href={alt.url || "https://www.zeno.health"} target="_blank" rel="noreferrer" className="text-xs font-bold text-primary hover:underline">
                        View on Zeno
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Alternative Medicines Section */}
        {alternatives && alternatives.length > 0 && (
          <div className="mt-8 mb-8">
            <div className="flex items-center gap-2 mb-6">
              <Replace className="h-6 w-6 text-primary" />
              <h2 className="font-bold text-2xl text-foreground">
                Alternative Medicines <span className="text-sm font-normal text-gray-500 ml-2">(Same Composition)</span>
              </h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
              {alternatives.map((alt: any) => (
                <ProductCard
                  key={alt.id}
                  name={alt.name}
                  slug={alt.slug}
                  category={alt.category}
                  composition={alt.composition}
                  image_url={alt.image_url}
                />
              ))}
            </div>
          </div>
        )}

      </div>
    </main>
  );
}
