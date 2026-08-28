import { useState } from 'react'
import { Combobox, ComboboxButton, ComboboxInput, ComboboxOption, ComboboxOptions } from '@headlessui/react'
import { Check, ChevronDown } from 'lucide-react'


const brandColors = {
  "BMW":            "#0066b1",
  "Mercedes-Benz":  "#1a1a1a",
  "Audi":           "#bb0a30",
  "Volkswagen":     "#1b3a6b",
  "Renault":        "#efdb00",
  "Fiat":           "#c5131e",
  "Ford":           "#003478",
  "Toyota":         "#eb0a1e",
  "Hyundai":        "#002c5f",
  "Honda":          "#cc0000",
  "Peugeot":        "#1f2c68",
  "Opel":           "#f2a900",
  "Nissan":         "#c3002f",
  "Citroen":        "#c40000",
  "Citroën":        "#c40000",
  "Dacia":          "#0068b3",
  "Kia":            "#05141f",
  "Skoda":          "#4ba82e",
  "Seat":           "#1a1a1a",
  "Cupra":          "#c2a46e",
  "Volvo":          "#003057",
  "Land Rover":     "#005a2b",
  "Jeep":           "#2b2b2b",
  "Porsche":        "#ae8040",
  "Mini":           "#1a1a1a",
  "Alfa Romeo":     "#8b0000",
  "Mazda":          "#910000",
  "Subaru":         "#003399",
  "Suzuki":         "#003087",
  "Chevrolet":      "#d4af37",
  "Mitsubishi":     "#cc0000",
  "Lexus":          "#1a1a1a",
  "Jaguar":         "#1a1a1a",
  "Maserati":       "#1c3d7a",
  "Ferrari":        "#cc0000",
  "MG":             "#cc0000",
  "BYD":            "#1a3a6b",
  "Chery":          "#cc0000",
  "Geely":          "#003087",
  "Tofaş":          "#cc0000",
  "KGM SsangYong":  "#003087",
  "DS Automobiles": "#c8a96e",
  "Daihatsu":       "#cc0000",
  "Ford - Otosan":  "#003478",
  "Ford Trucks":    "#003478",
  "Isuzu":          "#cc0000",
  "Iveco - Otoyol": "#003087",
  "DAF":            "#003580",
  "Lancia":         "#1a1a6e",
  "Lada":           "#cc0000",
  "BMC":            "#1a3a6b",
  "Temsa":          "#e85c0d",
  "Smart":          "#00a0dc",
  "Tesla":          "#cc0000",
  "TOGG":           "#c00d1e",
  "Seres":          "#1a1a1a",
  "Lamborghini":    "#d4af37",
  "Bentley":        "#1a472a",
  "Rolls-Royce":    "#1a1a1a",
  "Aston Martin":   "#004f3d",
  "Chrysler":       "#1a1a1a",
  "default":        "#4b5563",
};

// Turkish car color names → exact hex values (Hardcoded specific list)
const colorSwatches = {
  "Beyaz":          "#FFFFFF",
  "Siyah":          "#000000",
  "Gri":            "#9CA3AF",
  "Gümüş":          "#E5E7EB",
  "Füme":           "#4B5563",
  "Kırmızı":        "#EF4444",
  "Mavi":           "#3B82F6",
  "Lacivert":       "#1E3A8A",
  "Sarı":           "#EAB308",
  "Yeşil":          "#22C55E",
  "Bordo":          "#7F1D1D",
  "Kahverengi":     "#78350F",
  "Diğer":          "linear-gradient(135deg, #ef4444, #3b82f6, #22c55e)",
};

// Brand logo: uses open source car-logos-dataset, falls back to letter avatar on error
function BrandLogo({ brand }) {
  const [failed, setFailed] = useState(false);
  
  const slug = brand ? brand.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '') : '';
  const initial = brand ? brand[0].toUpperCase() : '?';
  const bgColor = brandColors[brand] || brandColors.default;

  // Fallback to initial if image failed to load or no brand provided
  if (!brand || failed) {
    return (
      <div
        className="w-6 h-6 shrink-0 rounded-md flex items-center justify-center text-white font-bold text-[10px] select-none"
        style={{ backgroundColor: bgColor }}
      >
        {initial}
      </div>
    );
  }

  return (
    <div className="w-6 h-6 shrink-0 flex items-center justify-center bg-white dark:bg-slate-600 rounded-md border border-slate-100 dark:border-slate-500 overflow-hidden p-0.5">
      <img
        src={`https://cdn.jsdelivr.net/gh/filippofilip95/car-logos-dataset@master/logos/optimized/${slug}.png`}
        className="w-full h-full object-contain"
        alt={brand}
        onError={() => setFailed(true)}
      />
    </div>
  );
}

// Color swatch box
function ColorSwatch({ colorName }) {
  const colorVal = colorSwatches[colorName];
  if (!colorVal) return (
    <div className="w-4 h-4 rounded-sm border border-slate-200 shrink-0 bg-transparent border-dashed" />
  );

  const isGradient = colorVal.includes('gradient');

  return (
    <div
      className="w-4 h-4 rounded-sm border border-slate-200 shrink-0"
      style={{
        background: isGradient ? colorVal : colorVal
      }}
    />
  );
}

export default function SearchableCombobox({
  options = [],
  value,
  onChange,
  placeholder = "Seçiniz",
  disabled = false,
  hasLogo = false,
  hasColor = false,
  name
}) {
  const [query, setQuery] = useState('')
  const safeOptions = Array.isArray(options) ? options : [];
  
  // Case-insensitive deduplication to remove duplicate brands like "Mini" and "MINI"
  const uniqueOptions = safeOptions.filter((val, i, arr) => 
    arr.findIndex(v => String(v).toLowerCase() === String(val).toLowerCase()) === i
  );

  const filteredOptions =
    query === ''
      ? uniqueOptions
      : uniqueOptions.filter((option) =>
          String(option).toLowerCase().includes(query.toLowerCase())
        )

  const selectedSwatch = hasColor && value ? colorSwatches[value] : null;
  const isSelectedGradient = selectedSwatch && selectedSwatch.includes('gradient');

  return (
    <div className="relative">
      <Combobox
        value={value}
        onChange={(val) => {
          setQuery('')
          onChange({ target: { name, value: val } })
        }}
        disabled={disabled}
      >
        {({ open }) => (
          <>
            <div className="relative w-full">
              <ComboboxButton className="w-full" as="div">
                <div className="relative flex items-center">
                  {selectedSwatch && (
                    <div
                      className="absolute left-3 w-4 h-4 rounded-sm border border-slate-200 shrink-0 z-10"
                      style={{
                        background: isSelectedGradient ? selectedSwatch : selectedSwatch
                      }}
                    />
                  )}
                  <ComboboxInput
                    className={`w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 pr-10 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 text-slate-800 dark:text-slate-100 cursor-pointer ${selectedSwatch ? 'pl-9' : ''}`}
                    displayValue={(option) => option || ''}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={disabled ? 'Önce üstteki alanı seçin' : placeholder}
                    autoComplete="off"
                  />
                </div>
              </ComboboxButton>
              <ComboboxButton className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <ChevronDown
                  className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
                  aria-hidden="true"
                />
              </ComboboxButton>
            </div>

            {safeOptions.length > 0 && (
              <ComboboxOptions
                anchor="bottom start"
                className="z-50 mt-1 max-h-60 overflow-y-auto custom-scrollbar w-[var(--input-width)] rounded-xl bg-white dark:bg-slate-800 py-1 text-base shadow-xl ring-1 ring-slate-200 dark:ring-slate-700 focus:outline-none sm:text-sm [--anchor-gap:4px]"
              >
                {filteredOptions.length === 0 && query !== '' ? (
                  <div className="relative cursor-default select-none py-2 px-4 text-slate-500 dark:text-slate-400 text-sm">
                    &ldquo;{query}&rdquo; bulunamadı.
                  </div>
                ) : (
                  filteredOptions.map((option) => (
                    <ComboboxOption
                      key={option}
                      value={option}
                      className={({ focus }) =>
                        `relative cursor-pointer select-none py-2.5 pl-3 pr-9 transition-colors ${
                          focus
                            ? 'bg-blue-50 dark:bg-slate-700 text-blue-700 dark:text-blue-300'
                            : 'text-slate-700 dark:text-slate-300'
                        }`
                      }
                    >
                      {({ selected }) => (
                        <>
                          <div className="flex items-center gap-2.5">
                            {hasLogo && <BrandLogo brand={option} />}
                            {hasColor && <ColorSwatch colorName={option} />}
                            <span className={`block truncate text-sm ${selected ? 'font-semibold text-blue-700 dark:text-blue-400' : 'font-normal'}`}>
                              {option}
                            </span>
                          </div>
                          {selected && (
                            <span className="absolute inset-y-0 right-0 flex items-center pr-3 text-blue-600 dark:text-blue-400">
                              <Check className="h-4 w-4" aria-hidden="true" />
                            </span>
                          )}
                        </>
                      )}
                    </ComboboxOption>
                  ))
                )}
              </ComboboxOptions>
            )}
          </>
        )}
      </Combobox>
    </div>
  )
}
