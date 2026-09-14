"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { Search, Upload, X, Loader2, Camera } from "lucide-react";

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

export default function LensSearchModal({ isOpen, onClose }: LensSearchModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [extractedText, setExtractedText] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

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

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      // Assuming backend is running on same origin or configured via next.config proxy
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/api/vision-search`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to scan image. Please try again.");
      }

      const data = await response.json();
      setResults(data.results || []);
      setExtractedText(data.extracted_text || []);
      
      if (data.results.length === 0 && data.extracted_text.length === 0) {
        setError("Could not find any recognizable medicine names in the image.");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred while scanning.");
    } finally {
      setIsScanning(false);
    }
  };

  const resetState = () => {
    setFile(null);
    setPreview(null);
    setResults([]);
    setExtractedText([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-2 text-indigo-600">
            <Camera className="w-5 h-5" />
            <h3 className="font-semibold text-gray-800">AI Lens Search</h3>
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
            <label 
              className="border-2 border-dashed border-indigo-200 rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-indigo-50/50 hover:border-indigo-400 transition-all group active:scale-95"
            >
              <div className="w-16 h-16 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Upload className="w-8 h-8" />
              </div>
              <p className="font-semibold text-indigo-700 mb-1 text-lg">Tap to Scan</p>
              <p className="text-sm text-gray-500 max-w-xs">Upload from gallery or take a new photo.</p>
              <input 
                type="file" 
                accept="image/*"
                className="hidden" 
                onChange={handleFileSelect}
              />
            </label>
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
          {!isScanning && results.length > 0 && (
            <div className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Matched Medicines</h4>
                <span className="text-xs text-indigo-600 font-medium bg-indigo-50 px-2 py-1 rounded-md">
                  Found: {extractedText.join(", ")}
                </span>
              </div>
              
              <div className="space-y-2">
                {results.map((product) => (
                  <Link 
                    key={product.id} 
                    href={`/product/${product.slug}`}
                    onClick={() => {
                      resetState();
                      onClose();
                    }}
                    className="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-md hover:border-indigo-100 transition-all group"
                  >
                    <div className="w-12 h-12 bg-gray-50 rounded-lg overflow-hidden flex items-center justify-center border border-gray-100 shrink-0">
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="w-10 h-10 object-contain mix-blend-multiply" />
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
              
              <div className="pt-2 text-center">
                <button onClick={resetState} className="text-sm font-medium text-gray-500 hover:text-indigo-600 transition-colors">
                  Scan another image
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Global CSS for scanning animation */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
    </div>
  );
}
