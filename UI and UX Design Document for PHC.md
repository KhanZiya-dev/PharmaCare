# **UI & UX Design Document (UXDD)**

**Project Name:** PharmaCare **Design Philosophy:** Trustworthy, Minimalist, Data-Driven. **Breakpoint Strategy:** Mobile (\<768px), Tablet (768px \- 1024px), Desktop (1024px+).

## **1\. Visual Identity & Styling**

> * **Color Palette:**  
  * **Primary:** Medical Blue (\#00236f) – Used for nav, hero text, and primary buttons.  
  * **Secondary:** Teal (\#006a61) – Used for savings, stock status, and positive indicators.  
  * **Background:** Off-white (\#f7f9fb) – Reduces eye strain.  
  * **Accent:** Soft gray (\#e0e3e5) for borders and subtle cards.  
> * **Typography:**  
  * **Headings:** DM Serif Display – Premium feel for the hero heading.  
  * **Body/Data:** Inter – High readability for prices and medicine composition.

## **2\. Layout Structure: Desktop (lg+)**

> * **Navigation:** Full-width glass-panel navbar.  
  * **Left:** Minimalist medical logo with text "PharmaCare".  
  * **Center:** Nav links (Medicines, Lab Tests, Price Trends).  
  * **Right:** WhatsApp Support button with business contact.  
> * **Hero Section:**  
  * Centered text with animate-word-pop effect ("Smart Prices", "For Better Health").  
  * **Left Floating Card:** Medicine comparison table (e.g., Pan-D Capsule) with "Save 15%" badge.  
  * **Right Floating Card:** Price trend monitor with SVG trend line.  
> * **Visual Anchor:**  
  * Bottom 3-panel grid (Lifestyle image, Pharmacist/Doctor portrait, Lab tech/Delivery service).  
  * Center image has the primary "Search Medicines" CTA button.

## 

## **3\. Layout Structure: Mobile (\<768px)**

> * **Navigation:** Compact mobile header.  
  * Logo remains top-left.  
  * Nav links collapse into a menu or scroll horizontally.  
  * Support button remains prominent.  
> * **Hero Section:**  
  * Text centered with reduced font size (headline-lg-mobile).  
  * Floating cards are stacked vertically below the hero heading.  
> * **Visual Anchor:**  
  * The 3-panel grid transitions to a simplified stack or vertical scroll to ensure image quality is preserved without cluttering the screen.

## **4\. Interaction & UX Polish**

> * **Micro-interactions:**  
  * **Buttons:** Subtle hover states (hover:-translate-y-1 and color transition).  
  * **Loading:** Skeleton loaders (shimmer effect) when fetching live prices from backend.  
  * **Animations:** fadeUp for cards and photoReveal for bottom images to guide the user's eye from top to bottom.  
> * **Trust Signals:**  
  * Green "Verified Data" badge on diagnostic/test cards.  
  * Clearly visible "Schedule H" warning badges for prescription-required drugs.

## **5\. Responsive Design Table**

| Element | Desktop (1024px+) | Mobile (\<768px) |
| :---- | :---- | :---- |
| **Navbar Links** | Visible horizontal list | Collapsed/Hamburger |
| **Floating Cards** | Absolute side positioning | Vertical stacking below hero |
| **Bottom Grid** | 3-panel wide flex | Simplified/Vertical stack |
| **Font Sizes** | display-lg (up to 4rem) | headline-lg-mobile (28px) |

