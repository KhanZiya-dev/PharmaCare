"use client";

import { ExternalLink, CheckCircle2, XCircle } from "lucide-react";

interface PlatformData {
  id: string;
  affiliate_url?: string;
  scrape_url: string;
  platforms: {
    name: string;
    logo_url?: string;
  };
  latest_price?: {
    mrp: number;
    selling_price: number;
    discount_pct: number;
    in_stock: boolean;
  };
}

interface ComparisonTableProps {
  platforms: PlatformData[];
}

export function ComparisonTable({ platforms }: ComparisonTableProps) {
  // Sort platforms by lowest selling price
  const sortedPlatforms = [...platforms].sort((a, b) => {
    const priceA = a.latest_price?.selling_price || Infinity;
    const priceB = b.latest_price?.selling_price || Infinity;
    return priceA - priceB;
  });

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-accent overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-accent/30 text-gray-600 text-sm border-b border-accent">
              <th className="p-4 font-semibold">Platform</th>
              <th className="p-4 font-semibold">Stock Status</th>
              <th className="p-4 font-semibold">Price</th>
              <th className="p-4 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {sortedPlatforms.map((platform, index) => {
              const hasPrice = !!platform.latest_price;
              const isLowest = index === 0 && hasPrice;
              const inStock = platform.latest_price?.in_stock ?? false;
              const targetUrl = platform.affiliate_url || platform.scrape_url;

              return (
                <tr 
                  key={platform.id} 
                  className={`border-b border-accent/50 hover:bg-accent/10 transition-colors ${
                    isLowest ? "bg-teal-50/30" : ""
                  }`}
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="font-bold text-foreground flex items-center gap-2">
                        {platform.platforms.name}
                        {isLowest && (
                          <span className="text-[10px] uppercase tracking-wider bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full font-bold">
                            Best Price
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  
                  <td className="p-4">
                    {hasPrice ? (
                      inStock ? (
                        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-teal-700">
                          <CheckCircle2 className="h-4 w-4" /> In Stock
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-red-600">
                          <XCircle className="h-4 w-4" /> Out of Stock
                        </span>
                      )
                    ) : (
                      <span className="text-gray-400 text-sm">Data unavailable</span>
                    )}
                  </td>
                  
                  <td className="p-4">
                    {hasPrice ? (
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-primary">
                            ₹{platform.latest_price!.selling_price}
                          </span>
                          {platform.latest_price!.discount_pct > 0 && (
                            <span className="text-xs font-bold text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
                              {platform.latest_price!.discount_pct}% OFF
                            </span>
                          )}
                        </div>
                        {platform.latest_price!.mrp > platform.latest_price!.selling_price && (
                          <span className="text-xs text-gray-400 line-through">
                            MRP ₹{platform.latest_price!.mrp}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  
                  <td className="p-4 text-right">
                    <a
                      href={`http://localhost:8000/redirect?mapping_id=${platform.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-full font-semibold transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 ${
                        isLowest 
                          ? "bg-primary text-white hover:bg-primary/90" 
                          : "bg-white border border-accent text-primary hover:bg-accent/20"
                      }`}
                    >
                      Buy Now
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </td>
                </tr>
              );
            })}
            
            {sortedPlatforms.length === 0 && (
              <tr>
                <td colSpan={4} className="p-8 text-center text-gray-500">
                  No pricing data available for this product yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
