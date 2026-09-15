"use client";

import { TrendingDown, TrendingUp, Activity, AlertCircle, Loader2, IndianRupee } from "lucide-react";
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
      
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 to-teal-500/5 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDuration: '8s' }} />

      {/* Card 1: Price Drop Alert */}
      <div className="pointer-events-auto absolute top-0 lg:top-12 left-1/2 -translate-x-1/2 lg:left-[-2rem] lg:translate-x-0 w-[90%] max-w-sm lg:w-72 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-green-100 p-4 lg:p-5 animate-bounce-slow hover:shadow-2xl hover:scale-105 transition-all z-10" style={{ animationDuration: '4s' }}>
        <Link href={`/product/${displayProducts[0].slug}`}>
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-green-100 p-1.5 rounded-full">
              <TrendingDown className="h-4 w-4 text-green-600" />
            </div>
            <span className="text-xs font-bold text-green-700 tracking-wide uppercase">Price Drop Alert</span>
          </div>
          <h3 className="font-bold text-foreground text-sm lg:text-base truncate w-full mb-1" title={displayProducts[0].name}>
            {displayProducts[0].name}
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-lg font-black text-green-600 tracking-tight">₹124</span>
            <span className="text-xs text-gray-400 line-through tabular-nums">₹180</span>
            <span className="text-[10px] font-bold bg-green-100 text-green-700 px-1.5 py-0.5 rounded ml-auto">
              31% OFF
            </span>
          </div>
        </Link>
      </div>

      {/* Center Display / Scanner graphic */}
      <div className="relative w-48 h-48 lg:w-64 lg:h-64 rounded-full border-4 border-dashed border-primary/20 flex items-center justify-center bg-white shadow-2xl mt-24 lg:mt-0 z-0">
        <div className="absolute inset-2 bg-gradient-to-b from-blue-50 to-indigo-50 rounded-full flex flex-col items-center justify-center p-4 text-center">
          <Scan className="h-10 w-10 text-primary mb-2 opacity-80" />
          <span className="text-xs font-bold text-primary uppercase tracking-widest">Scanning Prices</span>
          <span className="text-sm font-medium text-gray-500 mt-1 leading-tight">Across 10+ Pharmacies</span>
        </div>
      </div>

      {/* Card 2: Alternatives / Compare */}
      <div className="pointer-events-auto absolute bottom-0 lg:bottom-12 right-1/2 translate-x-1/2 lg:right-[-2rem] lg:translate-x-0 w-[90%] max-w-sm lg:w-72 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-indigo-100 p-4 lg:p-5 animate-bounce-slow hover:shadow-2xl hover:scale-105 transition-all z-10" style={{ animationDuration: '5s' }}>
        <Link href={`/product/${displayProducts[1].slug}`}>
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-50 p-2 rounded-lg">
                <IndianRupee className="h-5 w-5 text-indigo-500" />
              </div>
              <div>
                <h3 className="font-bold text-foreground text-sm lg:text-base truncate w-40" title={displayProducts[1].name}>
                  {displayProducts[1].name}
                </h3>
                <p className="text-[11px] text-gray-500 mt-0.5">High Price Variance Found</p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-500">Highest Price</span>
              <span className="font-semibold text-gray-700">₹65.00</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-500">Lowest Price</span>
              <span className="font-bold text-green-600">₹42.50</span>
            </div>
            {/* Visual Bar */}
            <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mt-1 flex">
              <div className="h-full bg-green-500 w-[65%]" />
              <div className="h-full bg-gray-300 w-[35%]" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-accent flex justify-between items-center">
            <p className="text-[11px] font-semibold text-green-600">Save up to 34%</p>
            <button className="bg-primary hover:bg-primary/90 text-white text-[11px] px-3 py-1.5 rounded font-bold transition-colors">
              Compare Now
            </button>
          </div>
        </Link>
      </div>

      {/* Price Trend Mini Card */}
      <div className="pointer-events-none hidden md:flex absolute top-1/2 -translate-y-1/2 right-4 lg:-right-12 bg-white/95 backdrop-blur-md rounded-full shadow-lg border border-accent px-5 py-3 items-center gap-3 animate-bounce-slow" style={{ animationDuration: '3.5s', animationDelay: '2s' }}>
        <div className="bg-blue-50 rounded-full p-1.5 flex items-center justify-center">
          <Activity className="h-4 w-4 text-blue-500" />
        </div>
        <span className="text-sm font-semibold text-gray-700 tracking-tight">Real-time Price Tracking</span>
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
