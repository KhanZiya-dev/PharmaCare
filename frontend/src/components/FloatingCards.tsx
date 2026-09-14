"use client";

import { TrendingDown, TrendingUp, Activity, Pill, AlertCircle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Product {
  id: string;
  name: string;
  slug: string;
  category: string;
}

export function FloatingCards() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/products`);
        if (res.ok) {
          const data = await res.json();
          // Keep only first 2 products for the cards
          setProducts(data.slice(0, 2));
        }
      } catch (err) {
        console.error("Failed to fetch products for floating cards", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProducts();
  }, []);

  // Fallback data if API fails or is empty
  const defaultProducts = [
    { name: "Pan-D Capsule", category: "medicine", slug: "pan-d-capsule", id: "1" },
    { name: "Dolo 650 Tablet", category: "medicine", slug: "dolo-650-tablet", id: "2" }
  ];

  const displayProducts = products.length >= 2 ? products : defaultProducts;

  return (
    <div className="relative w-full max-w-2xl mx-auto h-[450px] lg:h-[550px] flex items-center justify-center pointer-events-none">
      
      {/* Decorative Background Elements to fill empty space */}
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 to-teal-500/5 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDuration: '8s' }} />

      {/* Card 1: Medicine 1 */}
      <div className="pointer-events-auto absolute top-4 lg:top-12 left-0 lg:-left-8 w-64 lg:w-72 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-accent p-4 lg:p-5 animate-bounce-slow hover:shadow-2xl hover:scale-105 transition-all" style={{ animationDuration: '4s' }}>
        <Link href={`/product/${displayProducts[0].slug}`}>
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-bold text-foreground truncate w-40" title={displayProducts[0].name}>
                {displayProducts[0].name}
              </h3>
              <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                <Pill className="h-3 w-3" /> Medicine
              </p>
            </div>
            <span className="bg-teal-50 text-teal-700 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1">
              <TrendingDown className="h-3 w-3" />
              HOT
            </span>
          </div>
          <div className="flex justify-between items-end mt-4">
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Track live prices</p>
              <p className="text-sm font-semibold text-primary group-hover:underline">View Details &rarr;</p>
            </div>
            <div className="h-8 w-8 rounded-full bg-blue-50 flex items-center justify-center text-primary">
              <Activity className="h-4 w-4" />
            </div>
          </div>
        </Link>
      </div>

      {/* Card 2: Medicine 2 */}
      <div className="pointer-events-auto absolute bottom-8 lg:bottom-16 right-0 lg:-right-4 w-64 lg:w-80 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-accent p-4 lg:p-5 animate-bounce-slow hover:shadow-2xl hover:scale-105 transition-all" style={{ animationDuration: '5s', animationDelay: '1s' }}>
        <Link href={`/product/${displayProducts[1].slug}`}>
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-50 p-2 lg:p-3 rounded-lg hidden sm:block">
                <Pill className="h-5 w-5 text-indigo-500" />
              </div>
              <div>
                <h3 className="font-bold text-foreground text-sm lg:text-base truncate w-40" title={displayProducts[1].name}>
                  {displayProducts[1].name}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">Popular Search</p>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-accent flex justify-between items-center">
            <div>
              <p className="text-xs text-gray-500">Check alternatives</p>
            </div>
            <button className="bg-primary hover:bg-primary/90 text-white text-xs px-4 py-2 rounded-lg font-medium transition-colors shadow-sm">
              Compare
            </button>
          </div>
        </Link>
      </div>

      {/* Price Trend Mini Card (Desktop Only for better spacing) */}
      <div className="pointer-events-none hidden md:flex absolute top-1/2 -translate-y-1/2 right-4 lg:-right-12 bg-white/95 backdrop-blur-md rounded-full shadow-lg border border-accent px-5 py-3 items-center gap-3 animate-bounce-slow" style={{ animationDuration: '3.5s', animationDelay: '2s' }}>
        <div className="bg-orange-50 rounded-full p-1.5">
          <TrendingUp className="h-4 w-4 text-orange-500" />
        </div>
        <span className="text-sm font-semibold text-gray-700">Prices updated live</span>
      </div>
      
      {/* Floating Status Icon */}
      {isLoading && (
        <div className="absolute top-1/3 left-1/4 bg-white/80 p-2 rounded-full shadow-sm animate-pulse">
          <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
        </div>
      )}
    </div>
  );
}
