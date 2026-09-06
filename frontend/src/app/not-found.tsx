import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { SearchX, Home } from "lucide-react";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          {/* Large 404 */}
          <div className="relative mb-8">
            <span className="text-[120px] md:text-[160px] font-serif font-bold text-accent leading-none select-none">
              404
            </span>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-primary/10 p-4 rounded-full">
                <SearchX className="h-12 w-12 text-primary" />
              </div>
            </div>
          </div>

          <h1 className="font-serif text-2xl md:text-3xl font-bold text-primary mb-3">
            Page Not Found
          </h1>
          <p className="text-gray-500 mb-8 leading-relaxed">
            The page you&apos;re looking for doesn&apos;t exist or the medicine may have been removed from our catalog.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 bg-primary text-white px-6 py-3 rounded-full font-semibold hover:bg-primary/90 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
            >
              <Home className="h-4 w-4" />
              Go Home
            </Link>
            <Link
              href="/medicines"
              className="inline-flex items-center justify-center gap-2 bg-white border border-accent text-primary px-6 py-3 rounded-full font-semibold hover:bg-accent/20 transition-all"
            >
              Browse Medicines
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
