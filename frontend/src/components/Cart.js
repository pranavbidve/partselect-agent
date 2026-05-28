import React, { useState } from "react";
import "./Cart.css";

function Cart({ items }) {
  const [open, setOpen] = useState(false);
  const total = items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <div className="cart">
      <button className="cart-btn" onClick={() => setOpen(!open)}>
        <svg
          className="cart-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        {total > 0 && <span className="cart-badge">{total}</span>}
      </button>

      {open && (
        <div className="cart-dropdown">
          <p className="cart-title">Your Cart</p>
          {items.length === 0 ? (
            <p className="cart-empty">Cart is empty</p>
          ) : (
            <>
              <div className="cart-items">
                {items.map((item) => (
                  <div key={item.part_number} className="cart-item">
                    <span className="cart-item-name">{item.name}</span>
                    <span className="cart-item-qty">×{item.quantity}</span>
                  </div>
                ))}
              </div>
              <a
                href="https://www.partselect.com/shopping-cart/"
                target="_blank"
                rel="noopener noreferrer"
                className="cart-checkout"
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

export default Cart;
