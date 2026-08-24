"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

// Define the shape of search results based on backend schema
interface SearchResult {
  id: string;
  name: string;
  slug: string;
  category: string;
}

export function SearchAutocomplete() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search effect
  useEffect(() => {
    const fetchResults = async () => {
      if (query.trim().length < 2) {
        setResults([]);
        setIsOpen(false);
        return;
      }

      setIsLoading(true);
      setIsOpen(true);
      
      try {
        // In a real scenario, map this to your actual backend URL via env variables
        const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`);
        if (response.ok) {
          const data = await response.json();
          setResults(data);
        } else {
          setResults([]);
        }
      } catch (error) {
        console.error("Search error:", error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounceTimer = setTimeout(fetchResults, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      // Navigate to a search page or the first result if confident
      // For now, if we have results, just go to the first one, otherwise do nothing
      if (results.length > 0) {
        router.push(`/product/${results[0].slug}`);
        setIsOpen(false);
      }
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-2xl mx-auto z-40">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 h-5 w-5 text-gray-400" />
          <input
            type="text"
            className="w-full pl-12 pr-4 py-4 rounded-full border-2 border-accent bg-white focus:border-primary focus:ring-0 text-lg shadow-sm transition-colors outline-none"
            placeholder="Search for medicines or lab tests..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              if (query.length >= 2) setIsOpen(true);
            }}
          />
          {isLoading && (
            <Loader2 className="absolute right-4 h-5 w-5 text-primary animate-spin" />
          )}
        </div>
      </form>

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="absolute mt-2 w-full bg-white rounded-2xl shadow-xl border border-accent overflow-hidden">
          {results.length > 0 ? (
            <ul className="max-h-80 overflow-y-auto py-2">
              {results.map((result) => (
                <li key={result.id}>
                  <Link
                    href={`/product/${result.slug}`}
                    className="block px-4 py-3 hover:bg-accent/30 transition-colors"
                    onClick={() => setIsOpen(false)}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-foreground">{result.name}</span>
                      <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-1 rounded-full">
                        {result.category}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : query.length >= 2 && !isLoading ? (
            <div className="px-4 py-6 text-center text-gray-500">
              No results found for "{query}". Try checking the spelling.
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
