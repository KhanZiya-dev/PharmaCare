function extractSearchTermFromUrl(text) {
  try {
    const urlMatch = text.match(/https?:\/\/[^\s]+/);
    if (!urlMatch) return null;
    
    const urlStr = urlMatch[0];
    const url = new URL(urlStr);
    
    const domains = ["1mg.com", "netmeds.com", "apollopharmacy.in", "pharmeasy.in"];
    if (!domains.some(d => url.hostname.includes(d))) {
       return null; // Not a recognized pharmacy URL
    }

    const pathParts = url.pathname.split('/').filter(p => p.length > 0);
    if (pathParts.length === 0) return null;
    
    let slug = pathParts[pathParts.length - 1];
    
    // Remove IDs
    slug = slug.replace(/-[0-9]+$/, ''); 
    slug = slug.replace(/-otc[0-9]+$/, '');
    
    // Replace hyphens
    let searchTerm = slug.replace(/-/g, ' ');
    
    // Remove common packaging strings for cleaner search
    searchTerm = searchTerm.replace(/ strip of \d+ tablets?/, '');
    searchTerm = searchTerm.replace(/ \d+s$/, '');
    
    return searchTerm.trim();
  } catch (e) {
    return null;
  }
}

const tests = [
  "https://www.1mg.com/drugs/crocin-650-advance-tablet-136528",
  "https://www.1mg.com/otc/dolo-650-tablet-otc33433",
  "https://www.1mg.com/labs/test/complete-blood-count-cbc-123",
  "https://www.netmeds.com/prescriptions/dolo-650mg-tablet-15s",
  "https://www.apollopharmacy.in/otc/dolo-650-tablet",
  "https://pharmeasy.in/online-medicine-order/dolo-650mg-strip-of-15-tablets-44150",
  "This is a text with https://www.1mg.com/drugs/azithral-500-tablet-12345 in it"
];

for (const t of tests) {
  console.log(extractSearchTermFromUrl(t));
}
