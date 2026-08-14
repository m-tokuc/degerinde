"use client";
import { useState, useEffect } from "react";

const API_BASE_URL = "";

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
    Renk: "",
    Cekis: "",
    Kimden: "",
    Garanti_Durumu: "",
    Silindir_Sayisi: "",
    Koltuk_Sayisi: "",
    Motor_Hacmi_cc: "",
    Motor_Gucu_hp: "",
    Boya_Degisen: "",
    Tramer_TL: "",
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

  // Fetch initial options (brands)
  useEffect(() => {
    fetchOptions({});
  }, []);

  const fetchOptions = async (currentFilters) => {
    setLoadingOptions(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/dynamic_options`, {
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
    
    const next = { ...formData, [name]: value };
    
    // Cascading resets
    if (name === "Marka") {
      next.Seri = ""; next.Model = ""; next.Yil = "";
    } else if (name === "Seri") {
      next.Model = ""; next.Yil = "";
    } else if (name === "Model") {
      next.Yil = "";
    }

    setFormData(next);

    // Re-fetch dynamic options based on current hierarchical filters
    const filters = {};
    if (next.Marka) filters.Marka = next.Marka;
    if (next.Seri) filters.Seri = next.Seri;
    if (next.Model) filters.Model = next.Model;
    if (next.Yil) filters.Yil = parseInt(next.Yil, 10);
    if (next.Vites_Tipi) filters.Vites_Tipi = next.Vites_Tipi;
    if (next.Yakit_Tipi) filters.Yakit_Tipi = next.Yakit_Tipi;
    if (next.Kasa_Tipi) filters.Kasa_Tipi = next.Kasa_Tipi;

    fetchOptions(filters);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoadingPredict(true);
    setError(null);
    setResult(null);

    try {
      // Cast numeric fields properly to prevent Pydantic 422 errors
      const payload = {
        ...formData,
        Yil: parseInt(formData.Yil, 10) || 0,
        Kilometre: parseInt(formData.Kilometre, 10) || 0,
        Tramer_TL: parseFloat(formData.Tramer_TL) || 0,
        Motor_Hacmi_cc: formData.Motor_Hacmi_cc ? parseFloat(formData.Motor_Hacmi_cc) : null,
        Motor_Gucu_hp: formData.Motor_Gucu_hp ? parseFloat(formData.Motor_Gucu_hp) : null,
      };

      const res = await fetch(`${API_BASE_URL}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = "Değerleme sırasında bir hata oluştu.";
        if (errData.detail) {
          if (Array.isArray(errData.detail)) {
            errMsg = errData.detail.map(e => `${e.loc?.join('.') || 'Alan'}: ${e.msg}`).join(', ');
          } else if (typeof errData.detail === 'string') {
            errMsg = errData.detail;
          } else {
            errMsg = JSON.stringify(errData.detail);
          }
        }
        throw new Error(errMsg);
      }
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingPredict(false);
    }
  };

  const formatMoney = (val) => {
    if (!val && val !== 0) return "-";
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col">
      {/* Premium Header with Logo */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-8 h-8 text-blue-600" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="100" height="100" rx="20" fill="currentColor"/>
              <path d="M30 50 L45 65 L70 35" stroke="white" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M25 75 L75 75" stroke="white" strokeWidth="6" strokeLinecap="round" strokeOpacity="0.5"/>
            </svg>
            <span className="text-xl font-extrabold text-slate-900 tracking-tight">
              Değerinde<span className="text-blue-600">.</span>
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 lg:py-12 grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        {/* Left Side: Elaborate Form */}
        <div className="lg:col-span-7 bg-white p-6 md:p-8 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Araç Bilgilerini Girin</h1>
            <p className="text-slate-500 text-sm">Gelişmiş yapay zeka algoritmamız ile saniyeler içinde aracınızın piyasa değerini hesaplayın.</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            
            {/* Section 1: Basic Info */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wider mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs">1</span>
                Temel Bilgiler
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Marka *</label>
                  <select required name="Marka" value={formData.Marka} onChange={handleChange} disabled={loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Marka Seçin</option>
                    {options.Marka?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Seri *</label>
                  <select required name="Seri" value={formData.Seri} onChange={handleChange} disabled={!formData.Marka || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Seri Seçin</option>
                    {options.Seri?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Model / Donanım *</label>
                  <select required name="Model" value={formData.Model} onChange={handleChange} disabled={!formData.Seri || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Donanım Seçin</option>
                    {options.Model?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Yıl *</label>
                  <select required name="Yil" value={formData.Yil} onChange={handleChange} disabled={!formData.Model || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Yıl Seçin</option>
                    {options.Yil?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Kilometre *</label>
                  <input required type="number" name="Kilometre" min="0" value={formData.Kilometre} onChange={handleChange} placeholder="Örn: 85000" className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" />
                </div>
              </div>
            </div>

            <hr className="border-slate-100" />

            {/* Section 2: Technical Specs */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wider mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs">2</span>
                Teknik Özellikler
              </h3>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Yakıt Tipi</label>
                  <select name="Yakit_Tipi" value={formData.Yakit_Tipi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Yakit_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Vites Tipi</label>
                  <select name="Vites_Tipi" value={formData.Vites_Tipi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Vites_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Kasa Tipi</label>
                  <select name="Kasa_Tipi" value={formData.Kasa_Tipi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Kasa_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Motor Hacmi (cc)</label>
                  <select name="Motor_Hacmi_cc" value={formData.Motor_Hacmi_cc} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Motor_Hacmi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Motor Gücü (hp)</label>
                  <select name="Motor_Gucu_hp" value={formData.Motor_Gucu_hp} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Motor_Gucu?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Çekiş</label>
                  <select name="Cekis" value={formData.Cekis} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Cekis?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Silindir Sayısı</label>
                  <select name="Silindir_Sayisi" value={formData.Silindir_Sayisi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Silindir_Sayisi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Koltuk Sayısı</label>
                  <select name="Koltuk_Sayisi" value={formData.Koltuk_Sayisi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Koltuk_Sayisi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Renk</label>
                  <select name="Renk" value={formData.Renk} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Renk?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <hr className="border-slate-100" />

            {/* Section 3: Condition Details */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wider mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs">3</span>
                Ekspertiz ve Diğer Durumlar
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Boya / Değişen Durumu</label>
                  <select name="Boya_Degisen" value={formData.Boya_Degisen} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition">
                    <option value="">Belirsiz</option>
                    {options.Boya_Degisen?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Tramer Kaydı (TL)</label>
                  <input type="number" name="Tramer_TL" min="0" value={formData.Tramer_TL} onChange={handleChange} placeholder="Örn: 0" className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Kimden</label>
                  <select name="Kimden" value={formData.Kimden} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Kimden?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Garanti Durumu</label>
                  <select name="Garanti_Durumu" value={formData.Garanti_Durumu} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Garanti_Durumu?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <button type="submit" disabled={loadingPredict || !formData.Marka || !formData.Seri || !formData.Model || !formData.Yil || !formData.Kilometre} className="w-full mt-10 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition duration-200 shadow-xl shadow-blue-600/30 flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed">
              {loadingPredict ? "Hesaplanıyor..." : "Fiyatı Hesapla"}
            </button>
          </form>
        </div>

        {/* Right Side: Results */}
        <div className="lg:col-span-5 flex flex-col h-full sticky top-24">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-5 rounded-2xl mb-6 text-sm shadow-sm flex items-start gap-4">
              <span className="text-2xl shrink-0">⚠️</span>
              <div>
                <strong className="block font-bold mb-1">İşlem Başarısız</strong>
                {error}
              </div>
            </div>
          )}

          {loadingPredict && (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center border-2 border-slate-100 rounded-3xl p-10 text-center bg-white shadow-xl shadow-slate-200/50">
              <svg className="animate-spin h-12 w-12 text-blue-600 mb-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <h3 className="text-xl font-bold text-slate-800 mb-2">Yapay Zeka Analizi Başladı</h3>
              <p className="text-sm text-slate-500 max-w-xs mx-auto">
                Yapay zeka modelimiz milyonlarca piyasa verisini analiz ederek aracınızın en doğru değerini hesaplıyor...
              </p>
            </div>
          )}

          {!loadingPredict && result && result.status === "success" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Primary Price Card */}
              <div className="bg-white p-8 md:p-10 rounded-3xl shadow-2xl shadow-slate-200/60 border border-slate-100 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-2 bg-blue-600"></div>
                <p className="text-slate-500 text-sm font-bold uppercase tracking-widest mb-4">Değerinde. Tavsiye Edilen Satış Fiyatı</p>
                <h2 className="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
                  {formatMoney(result.predicted_price)}
                </h2>
                
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-slate-100">
                  <div className="text-left">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Tahmini Piyasa Fiyat Aralığı</p>
                    <p className="text-lg font-bold text-slate-700">{formatMoney(result.confidence_low)} <span className="text-slate-300 font-normal mx-1">-</span> {formatMoney(result.confidence_high)}</p>
                  </div>
                  <div className="hidden sm:block h-10 w-px bg-slate-200"></div>
                  <div className="text-right flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-sm font-semibold text-emerald-700">Yüksek Güvenilirlik</span>
                  </div>
                </div>
              </div>

              {/* Model Info */}
              <div className="bg-white p-6 rounded-3xl shadow-lg shadow-slate-200/50 border border-slate-100">
                <h3 className="text-sm font-bold text-slate-800 mb-4 px-2">Model Metrikleri & Şeffaflık</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-xs font-medium text-slate-500 mb-1">Algoritma</p>
                    <p className="text-sm font-bold text-slate-800">XGBoost Regressor</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-xs font-medium text-slate-500 mb-1">Başarı (R²)</p>
                    <p className="text-sm font-bold text-slate-800">%{(result.model_r2 * 100).toFixed(1)}</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-xs font-medium text-slate-500 mb-1">Ort. Hata (MAE)</p>
                    <p className="text-sm font-bold text-slate-800">± {formatMoney(result.mae)}</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-xs font-medium text-slate-500 mb-1">Analiz Edilen Özellik</p>
                    <p className="text-sm font-bold text-slate-800">{result.features_used} Kriter</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!loadingPredict && !result && !error && (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-3xl p-10 text-center bg-white/50">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-5">
                <svg className="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-slate-700 mb-3">Değerleme Sonucu</h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
                Aracınızın markasını, modelini ve tüm özelliklerini seçerek güncel ve doğru piyasa değerini öğrenebilirsiniz.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
