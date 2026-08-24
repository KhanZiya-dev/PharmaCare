import { TrendingDown, TrendingUp, Activity } from "lucide-react";

export function FloatingCards() {
  return (
    <div className="relative w-full max-w-lg mx-auto h-[400px]">
      {/* Medicine Comparison Card */}
      <div className="absolute top-0 left-0 w-64 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-accent p-4 animate-bounce-slow" style={{ animationDuration: '4s' }}>
        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="font-bold text-foreground">Pan-D Capsule</h3>
            <p className="text-xs text-gray-500">15 capsules</p>
          </div>
          <span className="bg-teal-50 text-teal-700 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            15% OFF
          </span>
        </div>
        <div className="flex justify-between items-end mt-4">
          <div>
            <p className="text-xs text-gray-400 line-through">₹199</p>
            <p className="text-xl font-bold text-primary">₹169</p>
          </div>
          <div className="text-xs text-gray-500 font-medium">1mg</div>
        </div>
      </div>

      {/* Lab Test Card */}
      <div className="absolute bottom-10 right-0 w-72 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-accent p-4 animate-bounce-slow" style={{ animationDuration: '5s', animationDelay: '1s' }}>
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center gap-2">
            <div className="bg-blue-50 p-2 rounded-lg">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-bold text-foreground text-sm">Full Body Checkup</h3>
              <p className="text-xs text-gray-500">Includes 65 tests</p>
            </div>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-accent flex justify-between items-center">
          <div>
            <p className="text-xs text-gray-500">Best Price</p>
            <p className="text-lg font-bold text-primary">₹799</p>
          </div>
          <button className="bg-primary hover:bg-primary/90 text-white text-xs px-4 py-2 rounded-lg font-medium transition-colors">
            Compare
          </button>
        </div>
      </div>

      {/* Price Trend Mini Card */}
      <div className="absolute top-32 right-12 bg-white/90 backdrop-blur-md rounded-full shadow-lg border border-accent px-4 py-2 flex items-center gap-2 animate-bounce-slow" style={{ animationDuration: '3.5s', animationDelay: '2s' }}>
        <TrendingUp className="h-4 w-4 text-orange-500" />
        <span className="text-xs font-medium">Prices updated live</span>
      </div>
    </div>
  );
}
