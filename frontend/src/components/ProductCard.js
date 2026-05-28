import React from "react";
import "./ProductCard.css";

function ProductCard({ part, onAddToCart }) {
  const { metadata } = part;
  const partSelectUrl = `https://www.partselect.com/PS${metadata.part_number.replace("PS", "")}-Part.htm`;

  return (
    <div className="product-card">
      <div className="product-icon">
        <img
          src={metadata.image_url}
          alt={metadata.name}
          className="product-img"
          onError={(e) => {
            e.target.src = `https://placehold.co/56x56/1b3875/ffffff?text=${encodeURIComponent(metadata.category)}&font=lato`;
          }}
        />
      </div>
      <div className="product-info">
        <div className="product-header">
          <div className="product-title-group">
            <p className="product-name">{metadata.name}</p>
            <p className="product-number">{metadata.part_number}</p>
          </div>
          <p className="product-price">${metadata.price.toFixed(2)}</p>
        </div>
        <div className="product-meta">
          {metadata.low_stock ? (
            <span className="stock-badge low-stock">
              Low Stock ({metadata.stock_level} left)
            </span>
          ) : (
            <span className="stock-badge in-stock">
              In Stock{metadata.stock_level != null ? ` (${metadata.stock_level})` : ""}
            </span>
          )}
          <span className="product-brand">{metadata.brand}</span>
        </div>
        <div className="product-actions">
          <button
            className="btn-add-cart"
            onClick={() => onAddToCart(metadata.part_number, metadata.name)}
          >
            Add to Cart
          </button>
          <a
            href={partSelectUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-view"
          >
            View on PartSelect
          </a>
        </div>
      </div>
    </div>
  );
}

export default ProductCard;
