import Link from "next/link";
import { Pill, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-white border-t border-accent mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Pill className="h-7 w-7 text-primary" />
              <span className="font-serif text-xl font-bold text-primary tracking-tight">
                PharmaCare
              </span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed max-w-sm mb-4">
              India&apos;s transparent medicine and lab test price aggregator. Compare prices across top e-pharmacies and never overpay again.
            </p>
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
              <p className="text-xs text-amber-800">
                <strong>Disclaimer:</strong> PharmaCare is an independent aggregator and does not sell or dispense medications directly. Always consult a healthcare professional before purchasing any medication.
              </p>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-bold text-foreground text-sm uppercase tracking-wider mb-4">
              Browse
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link href="/medicines" className="text-sm text-gray-500 hover:text-primary transition-colors">
                  Medicines
                </Link>
              </li>
              <li>
                <Link href="/lab-tests" className="text-sm text-gray-500 hover:text-primary transition-colors">
                  Lab Tests
                </Link>
              </li>
              <li>
                <Link href="/trends" className="text-sm text-gray-500 hover:text-primary transition-colors">
                  Price Trends
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="font-bold text-foreground text-sm uppercase tracking-wider mb-4">
              Support
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href="https://wa.me/1234567890"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-500 hover:text-[#25D366] transition-colors"
                >
                  WhatsApp Support
                </a>
              </li>
              <li>
                <span className="text-sm text-gray-500">
                  help@pharmacare.in
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-accent mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-gray-400">
            © {new Date().getFullYear()} PharmaCare. All rights reserved.
          </p>
          <p className="text-xs text-gray-400 flex items-center gap-1">
            Made with <Heart className="h-3 w-3 text-red-400 fill-red-400" /> in India
          </p>
        </div>
      </div>
    </footer>
  );
}
