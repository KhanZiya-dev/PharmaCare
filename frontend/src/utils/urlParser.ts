export function extractSearchTermFromUrl(text: string): string | null {
  try {
    const urlMatch = text.match(/https?:\/\/[^\s]+/);
    if (!urlMatch) return null;
    
    const urlStr = urlMatch[0];
    const url = new URL(urlStr);
    
    const domains = ["1mg.com", "netmeds.com", "apollopharmacy.in", "pharmeasy.in", "practo.com"];
    if (!domains.some(d => url.hostname.includes(d))) {
       return null; // Not a recognized pharmacy URL
    }

    const pathParts = url.pathname.split('/').filter(p => p.length > 0);
    if (pathParts.length === 0) return null;
    
    let slug = pathParts[pathParts.length - 1];
    
    // Remove typical IDs
    slug = slug.replace(/-[0-9]+$/, ''); 
    slug = slug.replace(/-otc[0-9]+$/, '');
    
    // Replace hyphens with space
    let searchTerm = slug.replace(/-/g, ' ');
    
    // Remove common packaging info at the end for broader search
    searchTerm = searchTerm.replace(/ strip of \d+ tablets?/, '');
    searchTerm = searchTerm.replace(/ \d+s$/, '');
    
    return searchTerm.trim();
  } catch (e) {
    return null;
  }
}
