"use client";

import { useState } from "react";

export interface CartItem {
  part_number: string;
  name: string;
  quantity: number;
}

interface Props {
  items: CartItem[];
}

export default function Cart({ items }: Props) {
  const [open, setOpen] = useState(false);
  const total = items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative flex items-center gap-1.5 text-white hover:text-blue-100 transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        {total > 0 && (
          <span className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center font-bold">
            {total}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50 p-4">
          <p className="font-semibold text-gray-900 mb-3">Your Cart</p>
          {items.length === 0 ? (
            <p className="text-sm text-gray-400">Cart is empty</p>
          ) : (
            <>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {items.map((item) => (
                  <div key={item.part_number} className="flex justify-between text-sm">
                    <span className="text-gray-700 truncate flex-1 mr-2">{item.name}</span>
                    <span className="text-gray-500 whitespace-nowrap">×{item.quantity}</span>
                  </div>
                ))}
              </div>
              <a
                href="https://www.partselect.com/shopping-cart/"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 block w-full text-center bg-[#0066CC] text-white py-2 rounded-lg text-sm font-medium hover:bg-[#0052a3] transition-colors"
              >
                Go to PartSelect Checkout →
              </a>
            </>
          )}
        </div>
      )}
    </div>
  );
}
