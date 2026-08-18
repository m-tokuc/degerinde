"use client";
import { useState, useEffect } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://degerinde.duckdns.org";

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
  const [loadingMessageIdx, setLoadingMessageIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const loadingMessages = [
    "Piyasa verileri taranıyor...",
    "Donanım özellikleri analiz ediliyor...",
    "Benzer ilanlar karşılaştırılıyor..."
  ];

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
        
        // Auto-select fields that have exactly 1 option and clear invalid ones
        setFormData(prev => {
          const next = { ...prev };
          let changed = false;
          
          const fieldMap = {
            Marka: "Marka", Seri: "Seri", Model: "Model", Yil: "Yil",
            Vites_Tipi: "Vites_Tipi", Yakit_Tipi: "Yakit_Tipi", Kasa_Tipi: "Kasa_Tipi",
            Renk: "Renk", Cekis: "Cekis", Motor_Hacmi: "Motor_Hacmi_cc",
            Motor_Gucu: "Motor_Gucu_hp", Garanti_Durumu: "Garanti_Durumu",
            Silindir_Sayisi: "Silindir_Sayisi", Koltuk_Sayisi: "Koltuk_Sayisi", Kimden: "Kimden"
          };
          
          Object.keys(fieldMap).forEach(optKey => {
            const formKey = fieldMap[optKey];
            const availableOptions = data[optKey] ? data[optKey].map(String) : [];
            
            // 1. If current value is not empty and not in the new options list, clear it
            if (next[formKey] && next[formKey] !== "" && next[formKey] !== "Belirsiz" && next[formKey] !== "Belirtilmemiş") {
              if (availableOptions.length > 0 && !availableOptions.includes(next[formKey].toString())) {
                next[formKey] = ""; // Reset to empty/default
                changed = true;
              }
            }
            
            // 2. Auto-select if exactly 1 option available
            if (availableOptions.length === 1) {
              const singleVal = availableOptions[0];
              if (next[formKey] !== singleVal) {
                next[formKey] = singleVal;
                changed = true;
              }
            }
          });
          
          return changed ? next : prev;
        });
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
    setLoadingMessageIdx(0);
    setError(null);
    setResult(null);

    const loaderInterval = setInterval(() => {
      setLoadingMessageIdx(prev => (prev + 1) % loadingMessages.length);
    }, 2000);

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
        throw new Error("Sunucu yanıt vermedi.");
      }
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Sunucuya bağlanılamadı, lütfen tekrar deneyin.");
    } finally {
      clearInterval(loaderInterval);
      setLoadingPredict(false);
    }
  };

  const handleKmChange = (e) => {
    const rawVal = e.target.value.replace(/\D/g, "");
    setFormData({...formData, Kilometre: rawVal});
  };

  const formatKm = (val) => {
    if (!val) return "";
    return parseInt(val, 10).toLocaleString('tr-TR');
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
            <svg className="w-10 h-10 text-blue-600" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 70 L30 70 L40 45 L70 45 L80 70 L95 70" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="30" cy="70" r="7" fill="white" stroke="currentColor" strokeWidth="5"/>
              <circle cx="80" cy="70" r="7" fill="white" stroke="currentColor" strokeWidth="5"/>
              <path d="M25 40 L45 20 L60 30 L85 10" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M70 10 L85 10 L85 25" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="text-2xl tracking-tight">
              <span className="font-extrabold text-blue-700">Değer</span><span className="font-medium text-slate-500">inde.</span>
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
                  <input required type="text" inputMode="numeric" name="Kilometre" value={formatKm(formData.Kilometre)} onChange={handleKmChange} placeholder="Örn: 85.000" className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:invalid:border-red-500 focus:invalid:ring-red-500 outline-none transition" />
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

            <button type="submit" disabled={loadingPredict || !formData.Marka || !formData.Seri || !formData.Model || !formData.Yil || !formData.Kilometre} className="w-full mt-10 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition duration-200 shadow-xl shadow-blue-600/30 flex justify-center items-center disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none disabled:cursor-not-allowed">
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
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center border-2 border-slate-100 rounded-3xl p-6 md:p-10 text-center bg-white shadow-xl shadow-slate-200/50">
              <div className="relative w-40 h-20 mb-8 mx-auto flex items-center justify-center overflow-hidden">
                <style>{`
                  @keyframes laser-sweep {
                    0% { left: 10%; opacity: 0; }
                    10% { opacity: 1; }
                    90% { opacity: 1; }
                    100% { left: 90%; opacity: 0; }
                  }
                `}</style>
                <svg className="w-full h-full text-slate-200" viewBox="0 0 100 50" fill="none">
                  <path d="M10 35 L20 35 L30 15 L70 15 L80 35 L90 35" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="25" cy="35" r="6" stroke="currentColor" strokeWidth="3"/>
                  <circle cx="75" cy="35" r="6" stroke="currentColor" strokeWidth="3"/>
                </svg>
                <div className="absolute top-2 bottom-2 w-1.5 bg-blue-500 rounded-full shadow-[0_0_15px_5px_rgba(59,130,246,0.8)]"
                     style={{ animation: 'laser-sweep 1.5s ease-in-out infinite alternate' }}>
                </div>
              </div>
              <h3 className="text-xl md:text-2xl font-bold text-slate-800 mb-2 transition-all duration-300">
                {loadingMessages[loadingMessageIdx]}
              </h3>
              <p className="text-sm text-slate-500 max-w-xs mx-auto">
                Yapay zeka modelimiz milyonlarca piyasa verisini analiz ediyor, lütfen bekleyin.
              </p>
            </div>
          )}

          {!loadingPredict && result && result.status === "success" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Outlier Warning */}
              {result.is_outlier && (
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-2xl flex items-start gap-3 text-amber-800 shadow-sm">
                  <svg className="w-6 h-6 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  <p className="text-sm font-medium">{result.outlier_warning}</p>
                </div>
              )}

              {/* Primary Price Card */}
              <div className="bg-white p-6 md:p-10 rounded-3xl shadow-2xl shadow-slate-200/60 border border-slate-100 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-2 bg-blue-600"></div>
                <p className="text-slate-500 text-xs md:text-sm font-bold uppercase tracking-widest mb-4">Değerinde. Tavsiye Edilen Satış Fiyatı</p>
                <h2 className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
                  {formatMoney(result.predicted_price)}
                </h2>
                
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-6 border-t border-slate-100">
                  <div className="text-center sm:text-left w-full sm:w-auto">
                    <p className="text-[10px] md:text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Tahmini Piyasa Fiyat Aralığı</p>
                    <p className="text-base md:text-lg font-bold text-slate-700 bg-slate-50 px-4 py-2 rounded-xl inline-block sm:block">
                      {formatMoney(result.confidence_low)} <span className="text-slate-300 font-normal mx-1">-</span> {formatMoney(result.confidence_high)}
                    </p>
                  </div>
                  <div className="hidden sm:block h-12 w-px bg-slate-200"></div>
                  <div className="text-center sm:text-right flex items-center justify-center gap-2 bg-emerald-50 px-4 py-2 rounded-xl w-full sm:w-auto">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs md:text-sm font-semibold text-emerald-700">Yüksek Güvenilirlik</span>
                  </div>
                </div>
              </div>

              {/* Explainable AI Breakdown */}
              {result.explanation && (
                <div className="bg-white p-6 rounded-3xl shadow-lg shadow-slate-200/50 border border-slate-100">
                  <h3 className="text-sm font-bold text-slate-800 mb-4 px-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                    Fiyat Neden Böyle Çıktı?
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl">
                      <span className="text-sm text-slate-600 font-medium">Model Taban Fiyatı</span>
                      <span className="font-bold text-slate-800">{formatMoney(result.explanation.base_average)}</span>
                    </div>
                    <div className="flex justify-between items-center bg-rose-50 p-3 rounded-xl">
                      <span className="text-sm text-rose-700 font-medium">Kilometre Etkisi</span>
                      <span className="font-bold text-rose-700">{formatMoney(result.explanation.km_impact)}</span>
                    </div>
                    <div className="flex justify-between items-center bg-orange-50 p-3 rounded-xl">
                      <span className="text-sm text-orange-700 font-medium">Yaş / Yıpranma Etkisi</span>
                      <span className="font-bold text-orange-700">{formatMoney(result.explanation.age_impact)}</span>
                    </div>
                    {result.explanation.damage_impact < 0 && (
                      <div className="flex justify-between items-center bg-red-50 p-3 rounded-xl">
                        <span className="text-sm text-red-700 font-medium">Hasar / Tramer Etkisi</span>
                        <span className="font-bold text-red-700">{formatMoney(result.explanation.damage_impact)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Model Info */}
              <div className="bg-white p-6 rounded-3xl shadow-lg shadow-slate-200/50 border border-slate-100">
                <h3 className="text-sm font-bold text-slate-800 mb-4 px-2">Model Metrikleri & Şeffaflık</h3>
                <div className="grid grid-cols-2 gap-3 md:gap-4">
                  <div className="bg-slate-50 p-3 md:p-4 rounded-2xl">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 mb-1">Algoritma</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800">XGBoost Regressor</p>
                  </div>
                  <div className="bg-slate-50 p-3 md:p-4 rounded-2xl">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 mb-1">Başarı (R²)</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800">%{(result.model_r2 * 100).toFixed(1)}</p>
                  </div>
                  <div className="bg-slate-50 p-3 md:p-4 rounded-2xl">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 mb-1">Ort. Hata (MAE)</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800">± {formatMoney(result.mae)}</p>
                  </div>
                  <div className="bg-slate-50 p-3 md:p-4 rounded-2xl">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 mb-1">Analiz Edilen Özellik</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800">{result.features_used} Kriter</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!loadingPredict && !result && !error && (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-3xl p-10 text-center bg-white/50">
              <div className="w-32 h-32 mb-6 flex items-center justify-center opacity-25 text-slate-600">
                <svg className="w-full h-full" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M20 70 A 40 40 0 1 1 80 70" strokeLinecap="round"/>
                  <path d="M30 60 L35 55 M50 40 L50 48 M70 60 L65 55" strokeLinecap="round"/>
                  <path d="M50 70 L75 55" stroke="currentColor" strokeWidth="5" strokeLinecap="round"/>
                  <circle cx="50" cy="70" r="6" fill="currentColor"/>
                  <circle cx="20" cy="70" r="3" fill="currentColor"/>
                  <circle cx="80" cy="70" r="3" fill="currentColor"/>
                  <circle cx="50" cy="30" r="4" fill="currentColor"/>
                  <path d="M50 30 L50 15 M50 30 L30 20 M50 30 L70 20" strokeWidth="2" strokeDasharray="4 4" />
                  <circle cx="50" cy="15" r="2" fill="currentColor"/>
                  <circle cx="30" cy="20" r="2" fill="currentColor"/>
                  <circle cx="70" cy="20" r="2" fill="currentColor"/>
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-700 mb-3">Değerleme Sonucu</h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
                Aracınızın markasını, modelini ve tüm özelliklerini seçerek güncel ve doğru piyasa değerini öğrenebilirsiniz.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Corporate Footer */}
      <footer className="mt-auto py-8 text-center text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col items-center justify-center gap-2">
          <p className="text-sm font-medium">© 2026 Değerinde. Tüm hakları saklıdır.</p>
          <p className="text-xs flex items-center gap-1 opacity-80">
            <svg className="w-3.5 h-3.5 text-blue-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            XGBoost Machine Learning algoritmaları ile desteklenmektedir.
          </p>
        </div>
      </footer>
    </div>
  );
}
