"use client";
import { useState } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    brand: "Renault",
    model: "Megane",
    trim: "1.5 dCi Touch",
    year: 2018,
    km: 120000,
    fuel_type: "Dizel",
    gear_type: "Otomatik",
    body_type: "Sedan",
    color: "Beyaz",
    seller: "Sahibinden",
    warranty: "Garantisi Yok",
    cylinders: "4 Silindir",
    boya_durumu: "Boyasız / Tamamı Orijinal",
    tramer_tl: 0,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: ["year", "km", "tramer_tl"].includes(name) ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/api/v2/predict_v2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Bir hata oluştu");
      }
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white font-sans p-6 md:p-12">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Left Side: Form */}
        <div className="bg-slate-800/50 p-8 rounded-2xl shadow-2xl border border-slate-700 backdrop-blur-sm">
          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">
            Yapay Zeka Araç Değerleme
          </h1>
          <p className="text-slate-400 mb-8 text-sm">Aracınızın özelliklerini girin, anında piyasa değerini öğrenin.</p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Marka</label>
                <input type="text" name="brand" value={formData.brand} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Seri (Model)</label>
                <input type="text" name="model" value={formData.model} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs text-slate-400 mb-1">Donanım / Paket</label>
                <input type="text" name="trim" value={formData.trim} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Yıl</label>
                <input type="number" name="year" value={formData.year} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Kilometre</label>
                <input type="number" name="km" value={formData.km} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Yakıt Tipi</label>
                <select name="fuel_type" value={formData.fuel_type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                  <option>Benzin</option><option>Dizel</option><option>LPG & Benzin</option><option>Hibrit</option><option>Elektrik</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Vites Tipi</label>
                <select name="gear_type" value={formData.gear_type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                  <option>Manuel</option><option>Otomatik</option><option>Yarı Otomatik</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Boya / Değişen</label>
                <select name="boya_durumu" value={formData.boya_durumu} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                  <option>Boyasız / Tamamı Orijinal</option><option>Belirsiz</option><option>Boyalı</option><option>Değişenli</option><option>Boyalı+Değişen</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Tramer (TL)</label>
                <input type="number" name="tramer_tl" value={formData.tramer_tl} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
              </div>
            </div>

            <button type="submit" disabled={loading} className="w-full mt-6 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-500 hover:to-teal-400 text-white font-semibold py-3 rounded-xl transition duration-300 shadow-lg shadow-blue-500/20 flex justify-center items-center">
              {loading ? "Hesaplanıyor..." : "Fiyatı Hesapla"}
            </button>
          </form>
        </div>

        {/* Right Side: Results */}
        <div className="flex flex-col justify-center">
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl mb-4 text-sm">
              🚨 {error}
            </div>
          )}

          {result && result.ui_formatted && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
              {/* Price Card */}
              <div className="bg-slate-800/80 p-8 rounded-2xl border border-blue-500/30 shadow-[0_0_40px_rgba(59,130,246,0.15)] text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-teal-400"></div>
                <p className="text-slate-400 text-sm uppercase tracking-wider mb-2">Tahmini İlan Fiyatı</p>
                <h2 className="text-5xl font-extrabold text-white mb-4">
                  {result.ui_formatted.price_range}
                </h2>
                <div className="inline-block bg-slate-900/50 rounded-full px-4 py-1 text-xs text-slate-400 border border-slate-700">
                  Model Versiyonu: {result.meta.version}
                </div>
              </div>

              {/* Value Adders */}
              {result.ui_formatted.value_adders && result.ui_formatted.value_adders.length > 0 && (
                <div className="bg-emerald-900/20 border border-emerald-500/30 p-6 rounded-2xl">
                  <h3 className="text-emerald-400 font-semibold mb-4 flex items-center gap-2">
                    <span className="text-xl">📈</span> Değer Artıran Özellikler
                  </h3>
                  <ul className="space-y-3">
                    {result.ui_formatted.value_adders.map((item, idx) => (
                      <li key={idx} className="flex justify-between items-center text-sm border-b border-emerald-500/10 pb-2 last:border-0 last:pb-0">
                        <span className="text-slate-300">{item.split(":")[0]}</span>
                        <span className="font-bold text-emerald-400">{item.split(":")[1]}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Value Reducers */}
              {result.ui_formatted.value_reducers && result.ui_formatted.value_reducers.length > 0 && (
                <div className="bg-rose-900/20 border border-rose-500/30 p-6 rounded-2xl">
                  <h3 className="text-rose-400 font-semibold mb-4 flex items-center gap-2">
                    <span className="text-xl">📉</span> Değer Düşüren Özellikler
                  </h3>
                  <ul className="space-y-3">
                    {result.ui_formatted.value_reducers.map((item, idx) => (
                      <li key={idx} className="flex justify-between items-center text-sm border-b border-rose-500/10 pb-2 last:border-0 last:pb-0">
                        <span className="text-slate-300">{item.split(":")[0]}</span>
                        <span className="font-bold text-rose-400">{item.split(":")[1]}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {!result && !error && (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-700 rounded-2xl p-12 text-center bg-slate-800/20">
              <span className="text-4xl mb-4">🤖</span>
              <p>Aracınızın bilgilerini doldurup<br/>yapay zeka analizini başlatın.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
