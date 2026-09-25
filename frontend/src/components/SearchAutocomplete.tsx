"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Search, Loader2, Camera, AlertCircle, Clock, Pill, Microscope, SearchX } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import LensSearchModal from "./LensSearchModal";

// --- Types ---
interface SearchAutocompleteProps {
  hideCameraIcon?: boolean;
  compact?: boolean;
}

interface SearchResult {
  id: string;
  name: string;
  slug: string;
  category: string;
  composition?: string;
  image_url?: string;
  match_type?: string; // "exact" | "prefix" | "fuzzy" | "composition"
  relevance?: number;
}

// --- Constants ---
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const CACHE_MAX_SIZE = 20;
const RECENT_SEARCHES_KEY = "pharmacare_recent_searches";
const MAX_RECENT_SEARCHES = 5;

// --- Cache (module-level, survives re-renders) ---
const searchCache = new Map<string, SearchResult[]>();

// --- Helpers ---
function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveRecentSearch(query: string) {
  if (typeof window === "undefined") return;
  try {
    const recent = getRecentSearches().filter((s) => s !== query);
    recent.unshift(query);
    localStorage.setItem(
      RECENT_SEARCHES_KEY,
      JSON.stringify(recent.slice(0, MAX_RECENT_SEARCHES))
    );
  } catch {
    // localStorage might be full or unavailable
  }
}

/** Wraps the matched substring in <mark> for highlighting */
function highlightMatch(text: string, query: string): React.ReactNode {
  if (!query || query.length < 2) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <strong className="text-primary font-bold">
        {text.slice(idx, idx + query.length)}
      </strong>
      {text.slice(idx + query.length)}
    </>
  );
}

/** Category badge component */
function CategoryBadge({ category }: { category: string }) {
  const isMedicine =
    category?.toLowerCase() === "medicine" ||
    category?.toLowerCase() === "prescription";
  const isLabTest =
    category?.toLowerCase() === "diagnostic" ||
    category?.toLowerCase() === "lab test" ||
    category?.toLowerCase() === "lab_test";

  if (isMedicine) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full shrink-0">
        <Pill className="w-3 h-3" />
        Medicine
      </span>
    );
  }
  if (isLabTest) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full shrink-0">
        <Microscope className="w-3 h-3" />
        Lab Test
      </span>
    );
  }
  return (
    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full shrink-0">
      {category}
    </span>
  );
}

// --- Main Component ---
export function SearchAutocomplete({ hideCameraIcon = false, compact = false }: SearchAutocompleteProps = {}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [isLensOpen, setIsLensOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [showRecent, setShowRecent] = useState(false);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const router = useRouter();
  const pathname = usePathname();

  const recentSearches = useMemo(() => getRecentSearches(), [showRecent]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setShowRecent(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll("li");
      items[highlightedIndex]?.scrollIntoView({ block: "nearest" });
    }
  }, [highlightedIndex]);

  // Debounced search with AbortController + Cache
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      setError(null);
      return;
    }

    const cacheKey = query.trim().toLowerCase();

    // Check cache first
    if (searchCache.has(cacheKey)) {
      setResults(searchCache.get(cacheKey)!);
      setIsOpen(true);
      setIsLoading(false);
      setError(null);
      setHighlightedIndex(-1);
      return;
    }

    setIsLoading(true);
    setIsOpen(true);
    setError(null);
    setHighlightedIndex(-1);

    const debounceTimer = setTimeout(async () => {
      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await fetch(
          `${API_URL}/search?q=${encodeURIComponent(query)}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`Search failed (${response.status})`);
        }

        const data: SearchResult[] = await response.json();
        setResults(data);
        setError(null);

        // Save to cache (evict oldest if full)
        if (searchCache.size >= CACHE_MAX_SIZE) {
          const firstKey = searchCache.keys().next().value;
          if (firstKey) searchCache.delete(firstKey);
        }
        searchCache.set(cacheKey, data);
      } catch (err: any) {
        if (err.name === "AbortError") return; // Request was cancelled, ignore
        console.error("Search error:", err);
        setResults([]);
        setError("Something went wrong. Please try again in a few seconds.");
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(debounceTimer);
    };
  }, [query]);

  // Keyboard navigation handler
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || results.length === 0) {
        // If showing recent searches, allow Enter to pick one
        if (showRecent && recentSearches.length > 0) {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlightedIndex((prev) =>
              prev < recentSearches.length - 1 ? prev + 1 : 0
            );
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlightedIndex((prev) =>
              prev > 0 ? prev - 1 : recentSearches.length - 1
            );
          } else if (e.key === "Enter" && highlightedIndex >= 0) {
            e.preventDefault();
            setQuery(recentSearches[highlightedIndex]);
            setShowRecent(false);
          } else if (e.key === "Escape") {
            setShowRecent(false);
            inputRef.current?.blur();
          }
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : 0
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : results.length - 1
          );
          break;
        case "Enter":
          e.preventDefault();
          if (highlightedIndex >= 0 && results[highlightedIndex]) {
            saveRecentSearch(query.trim());
            const target = results[highlightedIndex];
            router.push(target.category === "lab_test" ? `/lab-tests/${target.slug}` : `/product/${target.slug}`);
            setIsOpen(false);
          } else if (results.length > 0) {
            saveRecentSearch(query.trim());
            const target = results[0];
            router.push(target.category === "lab_test" ? `/lab-tests/${target.slug}` : `/product/${target.slug}`);
            setIsOpen(false);
          }
          break;
        case "Escape":
          setIsOpen(false);
          setHighlightedIndex(-1);
          inputRef.current?.blur();
          break;
      }
    },
    [isOpen, results, highlightedIndex, router, showRecent, recentSearches, query]
  );

  const handleResultClick = (slug: string) => {
    saveRecentSearch(query.trim());
    setIsOpen(false);
    setShowRecent(false);
  };

  const handleFocus = () => {
    if (query.length >= 2) {
      setIsOpen(true);
    } else if (recentSearches.length > 0) {
      setShowRecent(true);
      setHighlightedIndex(-1);
    }
  };

  const handleRecentClick = (search: string) => {
    setQuery(search);
    setShowRecent(false);
  };

  return (
    <>
      <div ref={wrapperRef} className="relative w-full max-w-2xl mx-auto z-40">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (results.length > 0) {
              const target =
                highlightedIndex >= 0 ? results[highlightedIndex] : results[0];
              saveRecentSearch(query.trim());
              router.push(target.category === "lab_test" ? `/lab-tests/${target.slug}` : `/product/${target.slug}`);
              setIsOpen(false);
            }
          }}
          className="relative"
        >
          <div className="relative flex items-center">
            <Search className={`absolute left-4 text-gray-400 ${compact ? 'h-4 w-4' : 'h-5 w-5'}`} />
            <input
              ref={inputRef}
              type="text"
              className={`w-full rounded-full border-2 border-accent bg-white focus:border-primary focus:ring-0 shadow-sm transition-colors outline-none ${
                compact ? "py-2.5 pl-10 pr-10 text-sm" : "pl-12 pr-14 py-4 text-lg"
              }`}
              placeholder={
                pathname?.startsWith('/lab-tests') 
                  ? "Search for lab tests..." 
                  : pathname?.startsWith('/medicines') || pathname?.startsWith('/product')
                    ? "Search for medicines..."
                    : "Search for medicines or lab tests..."
              }
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShowRecent(false);
              }}
              onFocus={handleFocus}
              onKeyDown={handleKeyDown}
              role="combobox"
              aria-expanded={isOpen || showRecent}
              aria-haspopup="listbox"
              aria-autocomplete="list"
              aria-activedescendant={
                highlightedIndex >= 0 ? `search-result-${highlightedIndex}` : undefined
              }
            />

            {!hideCameraIcon && (
              <button
                id="camera-search-button"
                type="button"
                onClick={() => setIsLensOpen(true)}
                className={`absolute bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100 transition-colors flex items-center justify-center ${
                  compact ? "right-1.5 w-7 h-7" : "right-3 p-2"
                }`}
                title="Search by Image"
              >
                <Camera className={compact ? "w-4 h-4" : "w-5 h-5"} />
              </button>
            )}
          </div>
        </form>

        {/* Recent Searches Dropdown */}
        <AnimatePresence>
          {showRecent && !isOpen && recentSearches.length > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="absolute mt-2 w-full bg-white rounded-2xl shadow-xl border border-accent overflow-hidden z-50 origin-top"
            >
              <div className="px-4 py-2.5 border-b border-gray-100">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Recent Searches
              </span>
            </div>
            <ul className="py-1" role="listbox">
              {recentSearches.map((search, idx) => (
                <li
                  key={search}
                  id={`recent-${idx}`}
                  role="option"
                  aria-selected={highlightedIndex === idx}
                  className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                    highlightedIndex === idx
                      ? "bg-indigo-50"
                      : "hover:bg-gray-50"
                  }`}
                  onClick={() => handleRecentClick(search)}
                >
                  <Clock className="w-4 h-4 text-gray-400 shrink-0" />
                  <span className="text-foreground">{search}</span>
                </li>
              ))}
            </ul>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Autocomplete Results Dropdown */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="absolute mt-2 w-full bg-white rounded-2xl shadow-xl border border-accent overflow-hidden z-50 origin-top"
            >
              {/* Error State */}
            {error ? (
              <div className="px-4 py-6 text-center">
                <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-red-500 text-sm font-medium mb-2">{error}</p>
                <button
                  onClick={() => {
                    setError(null);
                    searchCache.delete(query.trim().toLowerCase());
                    setQuery((q) => q + " "); // force re-fetch
                    setTimeout(() => setQuery((q) => q.trim()), 0);
                  }}
                  className="text-xs text-indigo-600 font-semibold hover:underline"
                >
                  Try again
                </button>
              </div>
            ) : results.length > 0 ? (
              <ul
                ref={listRef}
                className="max-h-96 overflow-y-auto py-2"
                role="listbox"
              >
                {results.map((result, idx) => (
                  <li
                    key={result.id}
                    id={`search-result-${idx}`}
                    role="option"
                    aria-selected={highlightedIndex === idx}
                  >
                    <Link
                      href={`/product/${result.slug}`}
                      className={`flex items-center gap-3 px-4 py-3 transition-colors ${
                        highlightedIndex === idx
                          ? "bg-indigo-50"
                          : "hover:bg-accent/30"
                      }`}
                      onClick={() => handleResultClick(result.slug)}
                    >
                      {/* Thumbnail */}
                      <div className="w-10 h-10 bg-gray-50 rounded-lg overflow-hidden flex items-center justify-center border border-gray-100 shrink-0">
                        {result.image_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={result.image_url}
                            alt=""
                            className="w-8 h-8 object-contain mix-blend-multiply"
                            loading="lazy"
                          />
                        ) : (
                          <Search className="w-4 h-4 text-gray-300" />
                        )}
                      </div>

                      {/* Name + composition */}
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-foreground block truncate">
                          {highlightMatch(result.name, query)}
                        </span>
                        {result.match_type === "composition" &&
                          result.composition && (
                            <span className="text-xs text-gray-400 block truncate">
                              Salt: {result.composition}
                            </span>
                          )}
                      </div>

                      {/* Category badge */}
                      <CategoryBadge category={result.category} />
                    </Link>
                  </li>
                ))}
              </ul>
            ) : query.length >= 2 && !isLoading ? (
              <div className="px-4 py-10 text-center flex flex-col items-center">
                <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center mb-3">
                  <SearchX className="w-6 h-6 text-indigo-300" />
                </div>
                <h3 className="text-sm font-semibold text-gray-800 mb-1">No results found</h3>
                <p className="text-xs text-gray-500 mb-4 max-w-[200px] mx-auto leading-relaxed">
                  We couldn&apos;t find &quot;<span className="font-medium text-gray-700">{query}</span>&quot;. Try checking the spelling or searching by salt composition.
                </p>
                <button 
                  onClick={() => setQuery("")}
                  className="text-xs font-medium text-indigo-600 bg-indigo-50 px-4 py-2 rounded-full hover:bg-indigo-100 transition-colors"
                >
                  Clear Search
                </button>
              </div>
            ) : null}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Lens Search Modal */}
      <LensSearchModal
        isOpen={isLensOpen}
        onClose={() => setIsLensOpen(false)}
      />
    </>
  );
}
