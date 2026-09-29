"use client";

import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";

export function BackButton() {
  const router = useRouter();
  const [backText, setBackText] = useState("Back to Search");
  const [backPath, setBackPath] = useState("/");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const from = sessionStorage.getItem("pharmacare_from");
      if (from === "/medicines") {
        setBackText("Back to Medicines");
        setBackPath("/medicines");
      } else if (from === "/lab-tests") {
        setBackText("Back to Lab Tests");
        setBackPath("/lab-tests");
      } else {
        setBackText("Back to Search");
        setBackPath("/");
      }
    }
  }, []);

  return (
    <Link 
      href={backPath}
      className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-primary transition-colors"
    >
      <ChevronLeft className="h-4 w-4 mr-1" />
      {backText}
    </Link>
  );
}
