import { Navbar } from "@/components/Navbar";
import { ComparisonTable } from "@/components/ComparisonTable";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { SearchAutocomplete } from "@/components/SearchAutocomplete";
import { AlertCircle, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

async function getProductData(slug: string) {
  try {
    // In production, map to the actual backend URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const res = await fetch(`${apiUrl}/product/${slug}`, {
      next: { revalidate: 60 } // Revalidate every minute
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

export default async function ProductPage({ params }: { params: { slug: string } }) {
  const data = await getProductData(params.slug);

  if (!data) {
    notFound();
  }

  const { product, platforms } = data;

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-8">
        
        {/* Top Navigation & Search */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <Link href="/" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-primary transition-colors">
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Search
          </Link>
          <div className="w-full md:w-96">
            <SearchAutocomplete />
          </div>
        </div>

        {/* Product Header */}
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-accent mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-start">
            {product.image_url ? (
              <img 
                src={product.image_url} 
                alt={product.name} 
                className="w-32 h-32 object-contain bg-gray-50 rounded-xl border border-accent p-2"
              />
            ) : (
              <div className="w-32 h-32 bg-gray-50 rounded-xl border border-accent flex items-center justify-center">
                <span className="text-gray-400 text-xs">No Image</span>
              </div>
            )}
            
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="font-serif text-3xl md:text-4xl font-bold text-primary">
                  {product.name}
                </h1>
                {product.requires_rx && (
                  <span className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 text-xs font-bold px-2.5 py-1 rounded-full border border-red-200">
                    <AlertCircle className="h-3 w-3" />
                    Prescription Required
                  </span>
                )}
              </div>
              
              <div className="text-sm font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 inline-block px-2 py-1 rounded-md mb-4">
                {product.category}
              </div>
              
              {product.composition && (
                <div>
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Composition</h4>
                  <p className="text-gray-700">{product.composition}</p>
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

      </div>
    </main>
  );
}
