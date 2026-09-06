import { Navbar } from "@/components/Navbar";

export default function ProductLoading() {
  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-8">
        {/* Back link skeleton */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div className="skeleton h-5 w-28" />
          <div className="skeleton h-12 w-full md:w-96 rounded-full" />
        </div>

        {/* Product Header skeleton */}
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-accent mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-start">
            <div className="skeleton w-32 h-32 rounded-xl" />
            <div className="flex-1 space-y-3">
              <div className="skeleton h-8 w-72" />
              <div className="skeleton h-6 w-24 rounded-md" />
              <div className="skeleton h-4 w-48" />
              <div className="skeleton h-4 w-64" />
            </div>
          </div>
        </div>

        {/* Content Grid skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Comparison Table skeleton */}
          <div className="lg:col-span-2 space-y-6">
            <div className="skeleton h-6 w-40 mb-4" />
            <div className="bg-white rounded-2xl shadow-sm border border-accent overflow-hidden">
              {/* Table header */}
              <div className="bg-accent/30 p-4 border-b border-accent">
                <div className="flex gap-8">
                  <div className="skeleton h-4 w-20" />
                  <div className="skeleton h-4 w-24" />
                  <div className="skeleton h-4 w-16" />
                  <div className="skeleton h-4 w-16 ml-auto" />
                </div>
              </div>
              {/* Table rows */}
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 border-b border-accent/50 flex items-center gap-8">
                  <div className="skeleton h-5 w-24" />
                  <div className="skeleton h-5 w-20" />
                  <div className="skeleton h-6 w-16" />
                  <div className="skeleton h-10 w-28 rounded-full ml-auto" />
                </div>
              ))}
            </div>
          </div>

          {/* Chart skeleton */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-accent p-6">
              <div className="skeleton h-6 w-48 mb-6" />
              <div className="skeleton h-[260px] w-full rounded-xl" />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
