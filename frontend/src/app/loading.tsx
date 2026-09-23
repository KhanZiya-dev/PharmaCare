
export default function HomeLoading() {
  return (
    <main className="min-h-screen bg-background flex flex-col">

      <div className="flex-1 max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full flex flex-col lg:flex-row items-center justify-center py-[clamp(3rem,8vw,6rem)] gap-[clamp(2rem,6vw,4rem)]">
        {/* Left: Text Content skeleton */}
        <div className="flex-1 w-full text-center lg:text-left">
          <div className="skeleton h-7 w-48 rounded-full mb-6 mx-auto lg:mx-0" />
          <div className="space-y-3 mb-8">
            <div className="skeleton h-14 w-80 max-w-full mx-auto lg:mx-0" />
            <div className="skeleton h-14 w-72 max-w-full mx-auto lg:mx-0" />
          </div>
          <div className="skeleton h-5 w-full max-w-lg mb-8 mx-auto lg:mx-0" />
          <div className="skeleton h-14 w-full max-w-xl rounded-full mx-auto lg:mx-0" />
        </div>

        {/* Right: Floating cards skeleton */}
        <div className="flex-1 w-full flex items-center justify-center">
          <div className="relative w-full max-w-2xl h-[450px]">
            <div className="skeleton absolute top-12 left-0 w-72 h-28 rounded-2xl" />
            <div className="skeleton absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full" />
            <div className="skeleton absolute bottom-12 right-0 w-72 h-44 rounded-2xl" />
          </div>
        </div>
      </div>

      {/* Bottom 3-panel Grid skeleton */}
      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] w-full pb-[clamp(2rem,6vw,4rem)]">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[clamp(1rem,4vw,1.5rem)]">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent h-56">
            <div className="flex items-center gap-3 mb-4">
              <div className="skeleton w-10 h-10 rounded-xl" />
              <div className="skeleton h-5 w-32" />
            </div>
            <div className="space-y-3">
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-3/4" />
            </div>
          </div>
          <div className="skeleton rounded-2xl h-56 md:-translate-y-4" />
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-accent h-56">
            <div className="flex items-center gap-3 mb-4">
              <div className="skeleton w-10 h-10 rounded-xl" />
              <div className="skeleton h-5 w-36" />
            </div>
            <div className="space-y-3">
              <div className="skeleton h-8 w-16" />
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-1.5 w-full rounded-full" />
            </div>
          </div>
        </div>
      </div>

    </main>
  );
}
