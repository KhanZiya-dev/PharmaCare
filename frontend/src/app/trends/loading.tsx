
export default function TrendsLoading() {
  return (
    <main className="min-h-screen bg-background flex flex-col">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-10">
        {/* Page Header skeleton */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="skeleton w-11 h-11 rounded-xl" />
            <div className="skeleton h-9 w-72" />
          </div>
          <div className="skeleton h-5 w-96 max-w-full" />
        </div>

        {/* How It Works Grid skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-accent">
              <div className="skeleton w-12 h-12 rounded-xl mb-4" />
              <div className="skeleton h-6 w-36 mb-2" />
              <div className="space-y-2">
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-4/5" />
              </div>
            </div>
          ))}
        </div>

        {/* Top Opportunities skeleton */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-6">
            <div className="skeleton w-10 h-10 rounded-xl" />
            <div className="skeleton h-7 w-64" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-accent overflow-hidden">
                <div className="skeleton h-40 w-full rounded-none" />
                <div className="p-4 space-y-2">
                  <div className="skeleton h-4 w-16 rounded-full" />
                  <div className="skeleton h-5 w-3/4" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
