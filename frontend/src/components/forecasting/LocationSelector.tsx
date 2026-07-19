'use client';

import React from 'react';

interface Location {
  location_id: number;
  ward: string;
  zone: string;
}

interface LocationSelectorProps {
  locations: Location[];
  selected: number;
  onSelect: (id: number) => void;
}

export default function LocationSelector({ locations, selected, onSelect }: LocationSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {locations.map(loc => (
        <button
          key={loc.location_id}
          onClick={() => onSelect(loc.location_id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            selected === loc.location_id
              ? 'bg-blue-600 text-white shadow-md'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {loc.ward}
        </button>
      ))}
    </div>
  );
}
