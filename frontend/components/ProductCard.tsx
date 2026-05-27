"use client";

interface Part {
  metadata: {
    part_number: string;
    name: string;
    price: number;
    stock_level: number;
    low_stock: boolean;
    image_url: string;
    brand: string;
    category: string;
    compatible_models: string;
  };
  description: string;
}

interface Props {
  part: Part;
  onAddToCart: (partNumber: string, name: string) => void;
}

export default function ProductCard({ part, onAddToCart }: Props) {
  const { metadata } = part;
  const partSelectUrl = `https://www.partselect.com/PS${metadata.part_number.replace("PS", "")}-Part.htm`;

  return (
    <div className="border border-gray-200 rounded-xl bg-white p-4 flex gap-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="w-16 h-16 rounded-lg border border-gray-100 bg-blue-50 flex-shrink-0 flex items-center justify-center">
        <span className="text-[#0066CC] font-bold text-xs text-center leading-tight px-1">{metadata.category}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-semibold text-gray-900 text-sm leading-tight">{metadata.name}</p>
            <p className="text-xs text-gray-500 font-mono mt-0.5">{metadata.part_number}</p>
          </div>
          <p className="text-[#0066CC] font-bold text-sm whitespace-nowrap">${metadata.price.toFixed(2)}</p>
        </div>

        <div className="flex items-center gap-2 mt-1.5">
          {metadata.low_stock ? (
            <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
              Low Stock ({metadata.stock_level} left)
            </span>
          ) : (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
              In Stock
            </span>
          )}
          <span className="text-xs text-gray-400">{metadata.brand}</span>
        </div>

        <div className="flex gap-2 mt-3">
          <button
            onClick={() => onAddToCart(metadata.part_number, metadata.name)}
            className="text-xs bg-[#0066CC] text-white px-3 py-1.5 rounded-lg hover:bg-[#0052a3] transition-colors font-medium"
          >
            Add to Cart
          </button>
          <a
            href={partSelectUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs border border-[#0066CC] text-[#0066CC] px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors font-medium"
          >
            View on PartSelect
          </a>
        </div>
      </div>
    </div>
  );
}
