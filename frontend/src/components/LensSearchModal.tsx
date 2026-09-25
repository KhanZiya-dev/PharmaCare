"use client";

import React, { useState, useRef } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { Search, Upload, X, Loader2, Camera, Image as ImageIcon, Pill, Droplets } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

interface LensSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SearchResult {
  id: string;
  name: string;
  slug: string;
  category: string;
  image_url: string | null;
}

interface ExtractedDetail {
  name: string;
  strength: string | null;
  form: string | null;
}

// Form icon + color mapping
const FORM_CONFIG: Record<string, { icon: string; color: string; bg: string; border: string }> = {
  Tablet:     { icon: "💊", color: "text-blue-700",   bg: "bg-blue-50",   border: "border-blue-200" },
  Capsule:    { icon: "💊", color: "text-indigo-700", bg: "bg-indigo-50", border: "border-indigo-200" },
  Syrup:      { icon: "🧪", color: "text-amber-700",  bg: "bg-amber-50",  border: "border-amber-200" },
  Suspension: { icon: "🧪", color: "text-amber-700",  bg: "bg-amber-50",  border: "border-amber-200" },
  Cream:      { icon: "🧴", color: "text-pink-700",   bg: "bg-pink-50",   border: "border-pink-200" },
  Gel:        { icon: "🧴", color: "text-purple-700", bg: "bg-purple-50", border: "border-purple-200" },
  Ointment:   { icon: "🧴", color: "text-pink-700",   bg: "bg-pink-50",   border: "border-pink-200" },
  Lotion:     { icon: "🧴", color: "text-rose-700",   bg: "bg-rose-50",   border: "border-rose-200" },
  Injection:  { icon: "💉", color: "text-red-700",    bg: "bg-red-50",    border: "border-red-200" },
  Drops:      { icon: "💧", color: "text-cyan-700",   bg: "bg-cyan-50",   border: "border-cyan-200" },
  Inhaler:    { icon: "🌬️", color: "text-teal-700",   bg: "bg-teal-50",   border: "border-teal-200" },
  Powder:     { icon: "⚗️", color: "text-orange-700", bg: "bg-orange-50", border: "border-orange-200" },
  Spray:      { icon: "💨", color: "text-sky-700",    bg: "bg-sky-50",    border: "border-sky-200" },
  Respules:   { icon: "🌬️", color: "text-teal-700",   bg: "bg-teal-50",   border: "border-teal-200" },
  Kit:        { icon: "🧰", color: "text-slate-700",  bg: "bg-slate-50",  border: "border-slate-200" },
  Sachet:     { icon: "📦", color: "text-emerald-700",bg: "bg-emerald-50",border: "border-emerald-200" },
};
const DEFAULT_FORM_CONFIG = { icon: "💊", color: "text-gray-700", bg: "bg-gray-50", border: "border-gray-200" };

function getFormConfig(form: string | null) {
  if (!form) return DEFAULT_FORM_CONFIG;
  return FORM_CONFIG[form] || DEFAULT_FORM_CONFIG;
}

// Module-level cache to persist scan results across page navigations
let cachedFile: File | null = null;
let cachedPreview: string | null = null;
let cachedResults: SearchResult[] = [];
let cachedExtractedText: string[] = [];
let cachedExtractedDetails: ExtractedDetail[] = [];
let cachedNotFound: string[] = [];
let cachedError: string | null = null;

export const getCachedScanResults = () => cachedResults;


export default function LensSearchModal({ isOpen, onClose }: LensSearchModalProps) {
  const [file, setFileState] = useState<File | null>(cachedFile);
  const [preview, setPreviewState] = useState<string | null>(cachedPreview);
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResultsState] = useState<SearchResult[]>(cachedResults);
  const [extractedText, setExtractedTextState] = useState<string[]>(cachedExtractedText);
  const [extractedDetails, setExtractedDetailsState] = useState<ExtractedDetail[]>(cachedExtractedDetails);
  const [notFound, setNotFoundState] = useState<string[]>(cachedNotFound);
  const [error, setErrorState] = useState<string | null>(cachedError);
  const [isDragging, setIsDragging] = useState(false);

  // Wrappers to update both local state and module cache
  const setFile = (val: File | null) => { cachedFile = val; setFileState(val); };
  const setPreview = (val: string | null) => { cachedPreview = val; setPreviewState(val); };
  const setResults = (val: SearchResult[]) => { cachedResults = val; setResultsState(val); };
  const setExtractedText = (val: string[]) => { cachedExtractedText = val; setExtractedTextState(val); };
  const setExtractedDetails = (val: ExtractedDetail[]) => { cachedExtractedDetails = val; setExtractedDetailsState(val); };
  const setNotFound = (val: string[]) => { cachedNotFound = val; setNotFoundState(val); };
  const setError = (val: string | null) => { cachedError = val; setErrorState(val); };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [mounted, setMounted] = useState(false);
  
  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    if (!selected.type.startsWith("image/")) {
      setError("Only image files are allowed. Please upload a valid image.");
      return;
    }

    setFile(selected);
    const objectUrl = URL.createObjectURL(selected);
    setPreview(objectUrl);
    
    // Automatically start scanning
    await handleUpload(selected);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const selected = e.dataTransfer.files?.[0];
    if (!selected) return;

    if (!selected.type.startsWith("image/")) {
      setError("Only image files are allowed. Please upload a valid image.");
      return;
    }

    setFile(selected);
    const objectUrl = URL.createObjectURL(selected);
    setPreview(objectUrl);
    
    // Automatically start scanning
    await handleUpload(selected);
  };

  const handleUpload = async (fileToUpload: File) => {
    setIsScanning(true);
    setError(null);
    setResults([]);
    setExtractedText([]);
    setExtractedDetails([]);
    setNotFound([]);

    const formData = new FormData();
    formData.append("file", fileToUpload);

    // 30-second timeout to handle Render cold starts
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/api/vision-search`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        try {
          const errData = await response.json();
          if (errData.detail) console.error("Scanner error:", errData.detail);
        } catch {
          // ignore
        }
        throw new Error("Unable to process this image right now. Please try again in a few seconds.");
      }

      const data = await response.json();
      setResults(data.results || []);
      setExtractedText(data.extracted_text || []);
      setExtractedDetails(data.extracted_details || []);
      setNotFound(data.not_found || []);
      
      if (data.results.length === 0 && (data.not_found || []).length === 0) {
        if (data.extracted_text.length === 0) {
          const msg = "Could not find any recognizable medicine names in the image.";
          setError(msg);
          toast.error(msg);
        }
      }
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        const msg = "Scan timed out. Please try again in a few seconds.";
        setError(msg);
        toast.error(msg);
      } else {
        const msg = err.message || "An error occurred. Please try again in a few seconds.";
        setError(msg);
        toast.error(msg);
      }
    } finally {
      setIsScanning(false);
    }
  };

  if (!mounted) return null;

  const resetState = () => {
    setFile(null);
    setPreview(null);
    setResults([]);
    setExtractedText([]);
    setExtractedDetails([]);
    setNotFound([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="relative w-[95vw] sm:w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
          >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-2 text-indigo-600">
            <Pill className="w-5 h-5" />
            <h3 className="font-semibold text-gray-800">Search by Dr. Prescription</h3>
          </div>
          <button 
            onClick={() => {
              resetState();
              onClose();
            }}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Upload Area */}
          {!preview ? (
            <div 
              className={`grid grid-cols-2 gap-4 p-4 -m-4 rounded-xl transition-colors border-2 border-dashed ${isDragging ? "border-indigo-500 bg-indigo-50/50" : "border-transparent"}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {/* Camera Button */}
              <label 
                className="border-2 border-dashed border-indigo-200 rounded-xl p-4 sm:p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-indigo-50/50 hover:border-indigo-400 transition-all group active:scale-95 bg-white shadow-sm"
              >
                <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Camera className="w-6 h-6" />
                </div>
                <p className="font-semibold text-indigo-700 mb-1 text-sm sm:text-base">Take Photo</p>
                <p className="text-xs text-gray-500">Open camera</p>
                <input 
                  type="file" 
                  accept="image/*"
                  capture="environment"
                  className="hidden" 
                  onChange={handleFileSelect}
                />
              </label>

              {/* Gallery Button */}
              <label 
                className="border-2 border-dashed border-indigo-200 rounded-xl p-4 sm:p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-indigo-50/50 hover:border-indigo-400 transition-all group active:scale-95 bg-white shadow-sm"
              >
                <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <ImageIcon className="w-6 h-6" />
                </div>
                <p className="font-semibold text-indigo-700 mb-1 text-sm sm:text-base">Gallery</p>
                <p className="text-xs text-gray-500">Upload image</p>
                <input 
                  type="file" 
                  accept="image/*"
                  className="hidden" 
                  onChange={handleFileSelect}
                />
              </label>
            </div>
          ) : (
            <div className="relative rounded-xl overflow-hidden bg-gray-100 border border-gray-200 aspect-video flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={preview} alt="Scan preview" className="object-contain w-full h-full" />
              
              {/* Scanning Overlay Animation */}
              {isScanning && (
                <div className="absolute inset-0 bg-indigo-900/20 backdrop-blur-[1px]">
                  <div className="absolute top-0 left-0 right-0 h-1 bg-indigo-400 shadow-[0_0_15px_rgba(129,140,248,0.8)] animate-[scan_2s_ease-in-out_infinite]" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-md px-4 py-2 rounded-full flex items-center gap-2 shadow-lg">
                      <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
                      <span className="text-sm font-semibold text-indigo-700 tracking-wide">Analyzing...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100 text-center">
               {error}
               <button onClick={resetState} className="ml-2 font-medium underline hover:text-red-700">Try again</button>
            </div>
          )}

          {/* Results State */}
          {!isScanning && (results.length > 0 || notFound.length > 0 || extractedText.length > 0) && !error && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Raw Extracted Text */}
              {extractedText.length > 0 && (
                <div className="p-3 bg-indigo-50/50 border border-indigo-100 rounded-xl">
                  <h4 className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Search className="w-3.5 h-3.5" /> Scanner Read:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {extractedText.map((text, idx) => (
                      <span key={idx} className="text-sm bg-white border border-indigo-200 text-indigo-700 px-2.5 py-1 rounded-md shadow-sm font-medium">
                        {text}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Prescription Detected — Rich Detail Cards */}
              {extractedDetails.length > 0 && (
                <div className="p-3 bg-gradient-to-br from-indigo-50/80 to-purple-50/40 border border-indigo-100 rounded-xl">
                  <h4 className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Pill className="w-3.5 h-3.5" /> Prescription Detected
                  </h4>
                  <div className="space-y-2">
                    {extractedDetails.map((detail, idx) => {
                      const fc = getFormConfig(detail.form);
                      return (
                        <div key={idx} className={`flex items-center gap-3 p-2.5 bg-white border ${fc.border} rounded-lg shadow-sm`}>
                          <div className={`w-9 h-9 ${fc.bg} rounded-lg flex items-center justify-center shrink-0 text-lg`}>
                            {fc.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-800 text-sm truncate">{detail.name}</p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              {detail.strength && (
                                <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                                  {detail.strength}
                                </span>
                              )}
                              {detail.form && (
                                <span className={`text-[11px] font-medium ${fc.color} ${fc.bg} px-1.5 py-0.5 rounded`}>
                                  {detail.form}
                                </span>
                              )}
                              {!detail.strength && !detail.form && (
                                <span className="text-[11px] text-gray-400 italic">Details not visible</span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {results.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Matched Medicines</h4>
                    <span className="text-xs text-indigo-600 font-medium bg-indigo-50 px-2 py-1 rounded-md">
                      {results.length} Found
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {results.map((product) => (
                      <Link 
                        key={product.id} 
                        href={`/product/${product.slug}`}
                        onClick={() => {
                          onClose();
                        }}
                        className="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-md hover:border-indigo-100 transition-all group"
                      >
                        <div className="w-12 h-12 bg-[#ffffff] rounded-lg overflow-hidden flex items-center justify-center border border-gray-100 shrink-0">
                          {product.image_url ? (
                            <img src={product.image_url} alt={product.name} className="w-10 h-10 object-contain" />
                          ) : (
                            <div className="text-xs text-gray-400 font-medium">Rx</div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-800 truncate group-hover:text-indigo-600 transition-colors">
                            {product.name}
                          </p>
                          <p className="text-xs text-gray-500 truncate capitalize">{product.category}</p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {notFound.length > 0 && (
                <div className="space-y-3 mt-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Not in Database</h4>
                    <span className="text-xs text-orange-600 font-medium bg-orange-50 px-2 py-1 rounded-md">
                      {notFound.length} Unmatched
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {notFound.map((name, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-100 rounded-xl">
                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200 shrink-0">
                          <X className="w-5 h-5 text-gray-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-600 truncate">{name}</p>
                          <p className="text-xs text-gray-400">Currently unavailable</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Disclaimer */}
              <div className="mt-4 p-3 bg-gray-50 rounded-xl border border-gray-100 flex items-start gap-2">
                <div className="text-gray-400 shrink-0 mt-0.5">
                  <Search className="w-4 h-4" />
                </div>
                <p className="text-[11px] leading-tight text-gray-500">
                  <strong className="text-gray-600">Disclaimer:</strong> The AI may sometimes misread handwritten prescriptions. Please verify the medicine names and consult your doctor before making any purchases.
                </p>
              </div>

              <div className="pt-2 text-center">
                <button onClick={resetState} className="text-sm font-medium text-indigo-500 hover:text-indigo-700 transition-colors">
                  Scan another image
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
      
      {/* Global CSS for scanning animation */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
        </motion.div>
      )}
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
}
