export function extractSearchTermFromUrl(text: string): string | null {
  try {
    let cleanText = text.trim();
    const domains = [
      "1mg.com",
      "netmeds.com",
      "apollopharmacy.in",
      "pharmeasy.in",
      "practo.com",
      "zeno.health",
      "zenohealth.com"
    ];

    // If user pasted without protocol, e.g. "pharmeasy.in/..." or "www.1mg.com/..."
    if (domains.some(d => cleanText.toLowerCase().includes(d)) && !/^https?:\/\//i.test(cleanText)) {
      cleanText = "https://" + cleanText;
    }

    const urlMatch = cleanText.match(/https?:\/\/[^\s]+/);
    if (!urlMatch) return null;
    
    const urlStr = urlMatch[0];
    const url = new URL(urlStr);
    
    if (!domains.some(d => url.hostname.toLowerCase().includes(d))) {
       return null; // Not a recognized pharmacy URL
    }

    const pathParts = url.pathname.split('/').filter(p => p.length > 0);
    if (pathParts.length === 0) return null;
    
    let slug = pathParts[pathParts.length - 1];
    
    // Remove typical numeric IDs at the end (e.g. -41635, -otc1234, -10023)
    slug = slug.replace(/-[0-9]+$/, ''); 
    slug = slug.replace(/-otc[0-9]+$/, '');
    
    // Replace hyphens with spaces
    let searchTerm = slug.replace(/-/g, ' ');
    
    // Remove packaging / count info for broader search
    searchTerm = searchTerm.replace(/\s+strip\s+of\s+\d+\s+tablets?/i, '');
    searchTerm = searchTerm.replace(/\s+\d+\s*'?s?$/i, '');
    searchTerm = searchTerm.replace(/\s+\d+\s+s$/i, '');
    
    return searchTerm.trim();
  } catch (e) {
    return null;
  }
}
