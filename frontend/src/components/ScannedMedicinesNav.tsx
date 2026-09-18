"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getCachedScanResults } from "./LensSearchModal";
import { FileText } from "lucide-react";

export function ScannedMedicinesNav() {
  const [scannedMedicines, setScannedMedicines] = useState<any[]>([]);
  const pathname = usePathname();

  useEffect(() => {
    // Only load the results if we have them cached
    const results = getCachedScanResults();
    if (results && results.length > 1) {
      setScannedMedicines(results);
    }
  }, []);

  if (scannedMedicines.length === 0) {
    return null;
  }

  // Current product slug
  const currentSlug = pathname.split("/").pop();

  return (
    <div className="w-full bg-white border border-indigo-100 shadow-sm rounded-xl p-3 mb-6 flex flex-col gap-2">
      <div className="flex items-center gap-2 text-indigo-700 text-xs font-semibold uppercase tracking-wider px-1">
        <FileText className="w-4 h-4" />
        Scanned Prescription Medicines
      </div>
      <div className="flex overflow-x-auto hide-scrollbar gap-2 pb-1">
        {scannedMedicines.map((med) => {
          const isActive = currentSlug === med.slug;
          return (
            <Link
              key={med.id}
              href={`/product/${med.slug}`}
              className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                isActive
                  ? "bg-indigo-600 text-white border-indigo-600 shadow-md"
                  : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700"
              }`}
            >
              {med.name}
            </Link>
          );
        })}
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}} />
    </div>
  );
}
