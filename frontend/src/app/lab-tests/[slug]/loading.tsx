
export default function LabTestLoading() {
  return (
    <main className="min-h-screen bg-gray-50/50 flex flex-col">

      <div className="flex-1 max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full py-[clamp(1.5rem,5vw,3rem)]">
        {/* Back link skeleton */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div className="skeleton h-5 w-28" />
          <div className="skeleton h-12 w-full md:w-96 rounded-full" />
        </div>

        {/* Product Header skeleton */}
        <div className="bg-white rounded-2xl p-5 md:p-6 shadow-sm border border-accent mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-start">
            <div className="skeleton w-24 h-24 rounded-xl hidden md:block" />
            <div className="flex-1 space-y-3 w-full">
              <div className="skeleton h-8 w-72 max-w-full" />
              <div className="flex gap-2">
                <div className="skeleton h-5 w-20 rounded-md" />
                <div className="skeleton h-5 w-32" />
              </div>
              <div className="flex gap-6 pt-4 border-t border-gray-100">
                <div className="space-y-1">
                  <div className="skeleton h-3 w-24" />
                  <div className="skeleton h-6 w-8" />
                </div>
                <div className="space-y-1">
                  <div className="skeleton h-3 w-24" />
                  <div className="skeleton h-6 w-16" />
                </div>
                <div className="space-y-1">
                  <div className="skeleton h-3 w-20" />
                  <div className="skeleton h-6 w-12" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Grid skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Comparison Table skeleton */}
          <div className="lg:col-span-2 space-y-6">
            <div className="skeleton h-7 w-40 mb-4" />
            <div className="bg-white rounded-2xl shadow-sm border border-accent overflow-hidden">
              <div className="bg-accent/30 p-4 border-b border-accent">
                <div className="flex gap-8">
                  <div className="skeleton h-4 w-20" />
                  <div className="skeleton h-4 w-24" />
                  <div className="skeleton h-4 w-16" />
                  <div className="skeleton h-4 w-16 ml-auto" />
                </div>
              </div>
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
