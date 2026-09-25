"use client";

import { Camera } from "lucide-react";

export function ScannerCTA() {
  return (
    <div 
      onClick={() => {
        const btn = document.getElementById('camera-search-button');
        if (btn) btn.click();
      }}
      className="bg-primary dark:bg-[#111111] rounded-2xl p-4 md:p-6 shadow-md border border-primary dark:border-[#333333] text-white dark:text-[#ffffff] flex flex-col justify-center items-center text-center transform md:-translate-y-4 cursor-pointer hover:bg-primary/90 dark:hover:bg-[#1a1a1a] transition-colors"
    >
      <h3 className="font-serif font-bold text-2xl mb-2">Have a Prescription?</h3>
      <p className="text-sm text-blue-100 dark:text-[#a3a3a3] mb-6 px-2">
        Don't manually search for each medicine. Scan your prescription and we'll compare the entire list at once.
      </p>
      <div className="bg-white/20 dark:bg-[#ffffff]/10 text-white dark:text-[#ffffff] font-bold py-2.5 px-6 rounded-full w-full shadow-sm flex items-center justify-center gap-2 border border-white/30 dark:border-[#ffffff]/20 hover:bg-white/30 dark:hover:bg-[#ffffff]/20 transition-colors">
        <Camera className="w-4 h-4" />
        Use the scanner above &uarr;
      </div>
    </div>
  );
}
