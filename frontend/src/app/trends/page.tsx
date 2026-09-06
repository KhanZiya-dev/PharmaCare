import { Navbar } from "@/components/Navbar";
import { TrendingDown, TrendingUp, BarChart3, Clock, ShieldCheck, ArrowRight } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Price Trends & Insights — PharmaCare",
  description: "Track medicine price trends, discover the best deals, and understand pricing patterns across top Indian e-pharmacies.",
};

export default function TrendsPage() {
  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-10">
        {/* Page Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="bg-blue-50 p-2.5 rounded-xl">
              <BarChart3 className="h-6 w-6 text-primary" />
            </div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold text-primary">
              Price Trends & Insights
            </h1>
          </div>
          <p className="text-gray-500 max-w-2xl">
            Understand pricing patterns, spot fake discounts with historical data, and make informed purchasing decisions.
          </p>
        </div>

        {/* How It Works Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent hover:shadow-md transition-shadow">
            <div className="bg-teal-50 p-3 rounded-xl inline-block mb-4">
              <Clock className="h-6 w-6 text-secondary" />
            </div>
            <h3 className="font-bold text-foreground text-lg mb-2">30-Day History</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              We track prices daily across all platforms. Every product page shows a 30-day price history chart so you can see the real trends.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent hover:shadow-md transition-shadow">
            <div className="bg-blue-50 p-3 rounded-xl inline-block mb-4">
              <ShieldCheck className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-bold text-foreground text-lg mb-2">Fake Discount Detector</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              Some platforms inflate MRP before showing discounts. Our historical data reveals the true pricing pattern so you never fall for it.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent hover:shadow-md transition-shadow">
            <div className="bg-green-50 p-3 rounded-xl inline-block mb-4">
              <TrendingDown className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="font-bold text-foreground text-lg mb-2">Best Time to Buy</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              Prices fluctuate based on demand, promotions, and supply. Our data helps you identify the best time to purchase your medications.
            </p>
          </div>
        </div>

        {/* Example Insights Section */}
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-accent mb-8">
          <h2 className="font-bold text-xl text-foreground mb-6">How to Read Our Charts</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="h-5 w-5 text-green-500" />
                <h3 className="font-bold text-foreground">Price Dropping</h3>
              </div>
              <div className="bg-green-50/50 rounded-xl p-4 border border-green-100">
                <p className="text-sm text-gray-600 leading-relaxed">
                  When you see a downward trend, it means the platform is genuinely reducing prices — possibly due to competition or a sale event. This is a <strong>good time to buy</strong>.
                </p>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-5 w-5 text-orange-500" />
                <h3 className="font-bold text-foreground">Price Inflating</h3>
              </div>
              <div className="bg-orange-50/50 rounded-xl p-4 border border-orange-100">
                <p className="text-sm text-gray-600 leading-relaxed">
                  An upward trend might indicate a supply shortage or an upcoming "fake discount" where MRP gets inflated. Compare with other platforms before buying.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-primary rounded-2xl p-8 text-center text-white">
          <h2 className="font-serif text-2xl md:text-3xl font-bold mb-3">
            Start Comparing Now
          </h2>
          <p className="text-blue-100 mb-6 max-w-lg mx-auto">
            Search for any medicine and view its price history chart. It&apos;s free, transparent, and always up-to-date.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/medicines"
              className="inline-flex items-center justify-center gap-2 bg-white text-primary px-6 py-3 rounded-full font-semibold hover:bg-gray-100 transition-colors shadow-sm"
            >
              Browse Medicines
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/lab-tests"
              className="inline-flex items-center justify-center gap-2 bg-white/10 border border-white/30 text-white px-6 py-3 rounded-full font-semibold hover:bg-white/20 transition-colors"
            >
              Browse Lab Tests
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
