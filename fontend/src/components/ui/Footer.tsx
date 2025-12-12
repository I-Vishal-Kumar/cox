'use client';

import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-cox-blue-600 to-cox-blue-800 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CA</span>
              </div>
              <div>
                <div className="text-white font-bold text-sm">Cox Automotive</div>
                <div className="text-xs text-gray-400">AI Analytics</div>
              </div>
            </div>
            <p className="text-xs text-gray-400">
              The industry's only end-to-end automotive services partner.
            </p>
          </div>

          {/* Our Brands */}
          <div>
            <h3 className="text-white font-semibold text-sm mb-3">Our Brands</h3>
            <ul className="space-y-2 text-xs">
              <li><Link href="#" className="hover:text-white transition-colors">Xtime</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Manheim</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Autotrader</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Dealer.com</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Kelley Blue Book</Link></li>
            </ul>
          </div>

          {/* Solutions */}
          <div>
            <h3 className="text-white font-semibold text-sm mb-3">Solutions</h3>
            <ul className="space-y-2 text-xs">
              <li><Link href="#" className="hover:text-white transition-colors">Fixed Ops</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Inventory</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Marketing</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Sales</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Fleet Solutions</Link></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-white font-semibold text-sm mb-3">Company</h3>
            <ul className="space-y-2 text-xs">
              <li><Link href="https://www.coxautoinc.com" target="_blank" className="hover:text-white transition-colors">About Cox Automotive</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Insights</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Contact</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center text-xs text-gray-400">
          <div>
            <p>© {new Date().getFullYear()} Cox Automotive. All Rights Reserved.</p>
            <p className="mt-1">A Division of Cox Enterprises</p>
          </div>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <Link href="https://www.coxautoinc.com" target="_blank" className="hover:text-white transition-colors">
              Privacy Statement
            </Link>
            <Link href="https://www.coxautoinc.com" target="_blank" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

