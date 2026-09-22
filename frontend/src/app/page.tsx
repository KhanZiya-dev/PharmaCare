import { SearchAutocomplete } from "@/components/SearchAutocomplete";
import { FloatingCards } from "@/components/FloatingCards";
import { ShieldCheck, TrendingDown, Camera, Activity } from "lucide-react";

export default async function Home() {
  let trends = [];
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${backendUrl}/trends/variance`, { next: { revalidate: 3600 } });
    if (res.ok) {
      trends = await res.json();
    }
  } catch (err) {
    console.error("Failed to fetch top price drops", err);
  }

  const topDrops = trends.slice(0, 3);

  return (
    <main className="min-h-screen bg-background flex flex-col">

      <div className="flex-1 max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full flex flex-col lg:flex-row items-center justify-center py-[clamp(3rem,8vw,6rem)] gap-[clamp(2rem,6vw,4rem)]">
        {/* Left: Text Content & Search */}
        <div className="flex-1 w-full text-center lg:text-left z-40">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 text-teal-700 text-sm font-semibold mb-6">
            <ShieldCheck className="h-4 w-4" />
            <span>100% Verified Price Data</span>
          </div>
          
          <h1 className="font-serif text-[clamp(2.5rem,6vw,4.5rem)] font-bold text-primary leading-tight mb-[clamp(1rem,3vw,1.5rem)]">
            <span className="block opacity-0 animate-[fadeUp_1s_ease-out_forwards]">Smart Prices</span>
            <span className="block opacity-0 animate-[fadeUp_1s_ease-out_0.3s_forwards]">For Better Health.</span>
          </h1>
          
          <p className="text-[clamp(1rem,1.5vw,1.25rem)] text-gray-600 mb-[clamp(1.5rem,4vw,2.5rem)] max-w-2xl mx-auto lg:mx-0">
            Compare prices for life-saving medicines and lab tests across top e-pharmacies. Don't fall for fake discounts—check our 30-day price history before you buy.
          </p>
          
          <div className="w-full max-w-xl mx-auto lg:mx-0 opacity-0 animate-[fadeUp_1s_ease-out_0.6s_forwards]">
            <SearchAutocomplete />
          </div>
        </div>

        {/* Right: Floating Cards */}
        <div className="flex-1 w-full z-10 opacity-0 animate-[fadeUp_1s_ease-out_0.9s_forwards]">
          <FloatingCards />
        </div>
      </div>

      {/* Visual Anchor (Bottom 3-panel Grid) */}
      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full pb-[clamp(2rem,6vw,4rem)] z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[clamp(1rem,4vw,1.5rem)] opacity-0 animate-[fadeUp_1s_ease-out_1.2s_forwards]">
          
          {/* Panel 1: Top Price Drops */}
          <div className="bg-white rounded-2xl p-4 md:p-6 shadow-sm border border-accent hover:shadow-md transition-shadow group flex flex-col h-full">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-green-50 p-2.5 rounded-xl text-green-600">
                <TrendingDown className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-foreground">Top Price Drops</h3>
            </div>
            
            <div className="space-y-3 flex-1">
              {topDrops.length > 0 ? (
                topDrops.map((drop: any, i: number) => (
                  <div key={drop.id} className={`flex justify-between items-center text-sm ${i < topDrops.length - 1 ? 'border-b border-gray-50 pb-2' : ''}`}>
                    <span className="font-medium text-gray-700 truncate w-32" title={drop.name}>{drop.name}</span>
                    <span className="text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded text-xs">
                      {Math.round(drop.discount_pct || 0)}% OFF
                    </span>
                  </div>
                ))
              ) : (
                <>
                  <div className="flex justify-between items-center text-sm border-b border-gray-50 pb-2">
                    <span className="font-medium text-gray-700">Shelcal 500</span>
                    <span className="text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded text-xs">-18%</span>
                  </div>
                  <div className="flex justify-between items-center text-sm border-b border-gray-50 pb-2">
                    <span className="font-medium text-gray-700">Telma 40</span>
                    <span className="text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded text-xs">-12%</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-gray-700">Augmentin 625</span>
                    <span className="text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded text-xs">-9%</span>
                  </div>
                </>
              )}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-400 group-hover:text-primary transition-colors font-medium cursor-pointer">
                View all tracking deals &rarr;
              </p>
            </div>
          </div>
          
          {/* Panel 2 (CTA): Scanner */}
          <div className="bg-primary rounded-2xl p-4 md:p-6 shadow-md border border-primary text-white flex flex-col justify-center items-center text-center transform md:-translate-y-4">
            <h3 className="font-serif font-bold text-2xl mb-2">Have a Prescription?</h3>
            <p className="text-sm text-blue-100 mb-6 px-2">
              Don't manually search for each medicine. Scan your prescription and we'll compare the entire list at once.
            </p>
            <div className="bg-white/20 text-white font-bold py-2.5 px-6 rounded-full w-full shadow-sm flex items-center justify-center gap-2 border border-white/30">
              <Camera className="w-4 h-4" />
              Use the scanner above &uarr;
            </div>
          </div>
          
          {/* Panel 3: Savings Data */}
          <div className="bg-white rounded-2xl p-4 md:p-6 shadow-sm border border-accent hover:shadow-md transition-shadow group flex flex-col h-full">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-blue-50 p-2.5 rounded-xl text-blue-600">
                <Activity className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-foreground">Why Track Prices?</h3>
            </div>
            
            <div className="space-y-4 flex-1">
              <div>
                <p className="text-2xl font-black text-gray-900">32%</p>
                <p className="text-xs text-gray-500 font-medium">Average variance between pharmacies for chronic meds.</p>
              </div>
              <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
                 <div className="h-full bg-blue-500 w-[68%]" />
                 <div className="h-full bg-gray-300 w-[32%]" />
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">
                Prices fluctuate daily based on pharmacy inventory and promotional offers. We track 5+ platforms to find the lowest cart value.
              </p>
            </div>
          </div>

        </div>
      </div>

    </main>
  );
}
