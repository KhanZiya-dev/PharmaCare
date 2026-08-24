import { Navbar } from "@/components/Navbar";
import { SearchAutocomplete } from "@/components/SearchAutocomplete";
import { FloatingCards } from "@/components/FloatingCards";
import { ShieldCheck, Stethoscope, Microscope } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-background flex flex-col relative overflow-hidden">
      <Navbar />

      <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex flex-col lg:flex-row items-center justify-center py-12 lg:py-24 gap-12">
        {/* Left: Text Content & Search */}
        <div className="flex-1 w-full text-center lg:text-left z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 text-teal-700 text-sm font-semibold mb-6">
            <ShieldCheck className="h-4 w-4" />
            <span>100% Verified Price Data</span>
          </div>
          
          <h1 className="font-serif text-5xl md:text-6xl lg:text-7xl font-bold text-primary leading-tight mb-6">
            <span className="block opacity-0 animate-[fadeUp_1s_ease-out_forwards]">Smart Prices</span>
            <span className="block opacity-0 animate-[fadeUp_1s_ease-out_0.3s_forwards]">For Better Health.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto lg:mx-0">
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pb-16 z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-0 animate-[fadeUp_1s_ease-out_1.2s_forwards]">
          
          {/* Panel 1 */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent hover:shadow-md transition-shadow group flex items-start gap-4">
            <div className="bg-blue-50 p-3 rounded-xl group-hover:bg-primary group-hover:text-white transition-colors text-primary">
              <Stethoscope className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-foreground mb-1">Medicines</h3>
              <p className="text-sm text-gray-500">Track prices for chronic medications and save up to 40% monthly.</p>
            </div>
          </div>
          
          {/* Panel 2 (CTA) */}
          <div className="bg-primary rounded-2xl p-6 shadow-md border border-primary text-white flex flex-col justify-center items-center text-center transform md:-translate-y-4">
            <h3 className="font-serif font-bold text-2xl mb-2">Ready to save?</h3>
            <p className="text-sm text-blue-100 mb-4">Start searching for your prescription above.</p>
            <button className="bg-white text-primary font-bold py-2 px-6 rounded-full w-full hover:bg-gray-100 transition-colors shadow-sm">
              Search Medicines
            </button>
          </div>
          
          {/* Panel 3 */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent hover:shadow-md transition-shadow group flex items-start gap-4">
            <div className="bg-teal-50 p-3 rounded-xl group-hover:bg-secondary group-hover:text-white transition-colors text-secondary">
              <Microscope className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-foreground mb-1">Lab Tests</h3>
              <p className="text-sm text-gray-500">Compare diagnostic packages from trusted labs in your city.</p>
            </div>
          </div>

        </div>
      </div>

      {/* Decorative background blur */}
      <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-blue-100/50 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-teal-50/50 rounded-full blur-3xl -z-10" />
    </main>
  );
}
