# Software Testing Report - PharmaCare

## 1. Introduction to Testing
Testing was a critical phase in the development of the PharmaCare platform to ensure that the data scraped from external sources is accurate, the backend APIs respond efficiently, and the user interface is intuitive and bug-free.

## 2. Types of Testing Performed

### 2.1 Unit Testing (Backend & Scraper)
Unit testing focuses on verifying that individual components of the system work as expected.
* **Scraper Accuracy Testing:** An automated script (`test_scraper_accuracy.py`) was developed using Playwright to test the extraction logic for various platforms (Apollo, 1mg, PharmEasy). It verifies if the extracted Selling Price, MRP, and Stock Status match the expected ranges.
  * **Result:** Passed (3/3 platforms successfully scraped). *(Include the terminal screenshot of scraper accuracy test here)*
* **API Endpoint Testing:** FastAPI's built-in Swagger UI (`/docs`) was used to independently test each API route (e.g., `GET /search`, `GET /products`). 
  * **Result:** APIs returned HTTP 200 OK with the correct JSON payload. *(Include the Swagger UI screenshot here)*

### 2.2 Integration Testing
Integration testing ensures that the Next.js Frontend successfully communicates with the FastAPI Backend, and the Backend successfully reads from the Supabase PostgreSQL database.
* The frontend search bar correctly triggers the backend `/search` API.
* The frontend gracefully handles loading states while the backend processes the request.
* Image URLs provided by the scraper are successfully rendered on the frontend.

---

## 3. Manual Test Cases

Below are the key manual test cases executed to validate the system requirements:

| Test ID | Module | Test Case Description | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Frontend | Enter a medicine name in the search bar and click Search. | System should display a list of matching medicines with images and prices. | Displayed correct list of medicines. | **PASS** |
| **TC-02** | Frontend | Click on a specific medicine from the search results. | Should navigate to the product detail page showing composition and available platforms. | Navigated to detail page with correct info. | **PASS** |
| **TC-03** | Frontend | View "Alternatives / Substitutes" section for a medicine. | System should suggest cheaper alternatives with the same chemical composition. | Alternatives displayed sorted by lowest price. | **PASS** |
| **TC-04** | Backend API | Send a `GET` request to `/search?q=Dolo` via Postman/Swagger. | API should return JSON array of products matching "Dolo" with HTTP 200 status. | Returned valid JSON with HTTP 200. | **PASS** |
| **TC-05** | Scraper | Run the Playwright background scraper for a specific URL. | Scraper should extract MRP, Selling Price, and Image URL accurately. | Correct data extracted bypassing bot protection. | **PASS** |
| **TC-06** | Database | Verify data insertion in `products` table in Supabase. | New scraped products should be visible in the Supabase Table Editor. | Data successfully populated in table. | **PASS** |
| **TC-07** | UI/UX | Test the website on a mobile device (Responsive Design). | Website layout should adjust to smaller screens automatically (Tailwind CSS). | UI adjusted perfectly on mobile viewport. | **PASS** |
| **TC-08** | Error Handling | Search for a random string (e.g., "xyzasd") that doesn't exist. | Frontend should show a friendly "No medicines found" message, not a system crash. | Displayed "No results found" correctly. | **PASS** |

## 4. Conclusion
The testing phase confirmed that the PharmaCare system is stable, the data acquisition from Apollo, 1mg, and PharmEasy is reliable, and the integration between Next.js, FastAPI, and Supabase functions seamlessly.
