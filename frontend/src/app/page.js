"use client";
import { useState, useEffect } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    Marka: "",
    Seri: "",
    Model: "",
    Yil: "",
    Kilometre: "",
    Vites_Tipi: "",
    Yakit_Tipi: "",
    Kasa_Tipi: "",
    Cekis: "",
    Renk: "",
    Kimden: "",
    Garanti_Durumu: "",
    Silindir_Sayisi: "",
    Koltuk_Sayisi: "",
    Motor_Hacmi_cc: "",
    Motor_Gucu_hp: "",
    Tramer_TL: "",
    Boya_Degisen: "",
  });

  const [options, setOptions] = useState({
    Marka: [], Seri: [], Model: [], Yil: [], Vites_Tipi: [], Yakit_Tipi: [],
    Kasa_Tipi: [], Renk: [], Cekis: [], Garanti_Durumu: [],
    Silindir_Sayisi: [], Koltuk_Sayisi: [], Kimden: [], Boya_Degisen: []
  });

  const [loadingOptions, setLoadingOptions] = useState(false);
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Initial load
  useEffect(() => {
    fetchOptions({});
  }, []);

  const fetchOptions = async (currentFilters) => {
    setLoadingOptions(true);
    try {
      const res = await fetch("/api/dynamic_options", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentFilters),
      });
      if (!res.ok) throw new Error("Seçenekler yüklenirken bir hata oluştu.");
      const data = await res.json();
      if (data.status === "success") {
        setOptions(data);
      }
    } catch (err) {
      console.error(err);
      setError("Bağlantı hatası: Araç verileri getirilemedi.");
    } finally {
      setLoadingOptions(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    setFormData((prev) => {
      const next = { ...prev, [name]: value };
      
      // Cascading logic
      if (name === "Marka") {
        next.Seri = ""; next.Model = ""; next.Yil = "";
      } else if (name === "Seri") {
        next.Model = ""; next.Yil = "";
      } else if (name === "Model") {
        next.Yil = "";
      }

      // Fetch dynamic options with updated hierarchical fields
      const filters = {};
      if (next.Marka) filters.Marka = next.Marka;
      if (next.Seri) filters.Seri = next.Seri;
      if (next.Model) filters.Model = next.Model;
      if (next.Yil) filters.Yil = Number(next.Yil);
      if (next.Vites_Tipi) filters.Vites_Tipi = next.Vites_Tipi;
      if (next.Yakit_Tipi) filters.Yakit_Tipi = next.Yakit_Tipi;
      if (next.Kasa_Tipi) filters.Kasa_Tipi = next.Kasa_Tipi;

      fetchOptions(filters);
      
      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoadingPredict(true);
    setError(null);
    setResult(null);

    try {
      // Cast numeric fields properly to avoid Pydantic 422 errors
      const payload = {
        ...formData,
        Yil: parseInt(formData.Yil, 10) || 0,
        Kilometre: parseInt(formData.Kilometre, 10) || 0,
        Tramer_TL: parseFloat(formData.Tramer_TL) || 0,
        Motor_Hacmi_cc: formData.Motor_Hacmi_cc ? parseFloat(formData.Motor_Hacmi_cc) : null,
        Motor_Gucu_hp: formData.Motor_Gucu_hp ? parseFloat(formData.Motor_Gucu_hp) : null,
      };

      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Değerleme sırasında bir hata oluştu.");
      }
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingPredict(false);
    }
  };

  // UI Helper: formatting currency
  const formatMoney = (val) => {
    if (!val && val !== 0) return "-";
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans p-4 md:p-8 lg:p-12">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Form */}
        <div className="lg:col-span-7 bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-200">
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Değerinde<span className="text-blue-600">.</span>
            </h1>
            <p className="text-slate-500 mt-2 text-sm">Gelişmiş yapay zeka algoritması ile aracınızın güncel piyasa değerini saniyeler içinde hesaplayın.</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Primary Features */}
            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-2">Temel Araç Bilgileri</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Marka *</label>
                  <select required name="Marka" value={formData.Marka} onChange={handleChange} disabled={loadingOptions} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50">
                    <option value="">Seçiniz</option>
                    {options.Marka?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Seri *</label>
                  <select required name="Seri" value={formData.Seri} onChange={handleChange} disabled={!formData.Marka || loadingOptions} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50">
                    <option value="">Seçiniz</option>
                    {options.Seri?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-600 mb-1">Model / Donanım *</label>
                  <select required name="Model" value={formData.Model} onChange={handleChange} disabled={!formData.Seri || loadingOptions} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50">
                    <option value="">Seçiniz</option>
                    {options.Model?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Yıl *</label>
                  <select required name="Yil" value={formData.Yil} onChange={handleChange} disabled={!formData.Model || loadingOptions} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50">
                    <option value="">Seçiniz</option>
                    {options.Yil?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Kilometre *</label>
                  <input required type="number" name="Kilometre" min="0" max="1000000" value={formData.Kilometre} onChange={handleChange} placeholder="Örn: 120000" className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" />
                </div>
              </div>
            </div>

            {/* Technical Details */}
            <div className="space-y-4 px-2">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-2">Teknik Detaylar</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Yakıt Tipi</label>
                  <select name="Yakit_Tipi" value={formData.Yakit_Tipi} onChange={handleChange} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Yakit_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Vites Tipi</label>
                  <select name="Vites_Tipi" value={formData.Vites_Tipi} onChange={handleChange} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Vites_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Kasa Tipi</label>
                  <select name="Kasa_Tipi" value={formData.Kasa_Tipi} onChange={handleChange} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Kasa_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Renk</label>
                  <select name="Renk" value={formData.Renk} onChange={handleChange} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Renk?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Condition Details */}
            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-2">Ekspertiz Durumu</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Boya / Değişen Durumu</label>
                  <select name="Boya_Degisen" value={formData.Boya_Degisen} onChange={handleChange} className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition">
                    <option value="">Belirsiz</option>
                    {options.Boya_Degisen?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Tramer Kaydı (TL)</label>
                  <input type="number" name="Tramer_TL" min="0" value={formData.Tramer_TL} onChange={handleChange} placeholder="Örn: 0" className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition" />
                </div>
              </div>
            </div>

            <button type="submit" disabled={loadingPredict || !formData.Marka || !formData.Seri || !formData.Model || !formData.Yil || !formData.Kilometre} className="w-full mt-8 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl transition duration-200 shadow-md shadow-blue-600/20 flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed">
              {loadingPredict ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Hesaplanıyor...
                </span>
              ) : "Değerlemeyi Başlat"}
            </button>
          </form>
        </div>

        {/* Right Side: Results */}
        <div className="lg:col-span-5 flex flex-col h-full">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl mb-6 text-sm shadow-sm flex items-start gap-3">
              <span className="text-xl shrink-0">⚠️</span>
              <div>
                <strong className="block font-semibold mb-1">İşlem Başarısız</strong>
                {error}
              </div>
            </div>
          )}

          {result && result.status === "success" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Primary Price Card */}
              <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-100 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-600 to-emerald-500"></div>
                <p className="text-slate-500 text-xs font-semibold uppercase tracking-widest mb-3">Yapay Zeka Değerlemesi</p>
                <h2 className="text-5xl font-extrabold text-slate-900 tracking-tight mb-2">
                  {formatMoney(result.predicted_price)}
                </h2>
                <div className="flex items-center justify-center gap-2 mt-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                    Yüksek Güvenilirlik
                  </span>
                </div>
              </div>

              {/* Confidence Interval */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  Tahmin Aralığı
                </h3>
                <div className="flex justify-between items-end">
                  <div className="text-left">
                    <p className="text-xs text-slate-500 mb-1">Minimum Değer</p>
                    <p className="text-lg font-bold text-slate-700">{formatMoney(result.confidence_low)}</p>
                  </div>
                  <div className="flex-1 px-4 hidden sm:flex items-center">
                    <div className="h-2 w-full bg-gradient-to-r from-slate-200 via-blue-200 to-slate-200 rounded-full"></div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 mb-1">Maksimum Değer</p>
                    <p className="text-lg font-bold text-slate-700">{formatMoney(result.confidence_high)}</p>
                  </div>
                </div>
              </div>

              {/* Model Info */}
              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
                <h3 className="text-sm font-semibold text-slate-800 mb-3">Model Metrikleri</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500">Algoritma</p>
                    <p className="text-sm font-medium text-slate-700">XGBoost Regressor</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">R² Skoru (Başarı)</p>
                    <p className="text-sm font-medium text-slate-700">%{(result.model_r2 * 100).toFixed(1)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Hata Payı (MAE)</p>
                    <p className="text-sm font-medium text-slate-700">± {formatMoney(result.mae)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Değerlendirilen Kriter</p>
                    <p className="text-sm font-medium text-slate-700">{result.features_used} Özellik</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!result && !error && (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl p-8 text-center bg-white/50">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path></svg>
              </div>
              <h3 className="text-lg font-medium text-slate-600 mb-2">Değerleme Sonucu</h3>
              <p className="text-sm max-w-xs mx-auto">
                Aracınızın markasını, modelini ve özelliklerini seçerek güncel piyasa değerini öğrenebilirsiniz.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
