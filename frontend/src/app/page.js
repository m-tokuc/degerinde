"use client";
import { useState, useEffect } from "react";
import { toast } from 'react-hot-toast';

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
  const [autoFilledFields, setAutoFilledFields] = useState({});

  const initialAppraisal = {
    sol_on_camurluk: 0, kaput: 0, sag_on_camurluk: 0, tavan: 0,
    sol_on_kapi: 0, sag_on_kapi: 0, sol_arka_kapi: 0, sag_arka_kapi: 0,
    sol_arka_camurluk: 0, bagaj: 0, sag_arka_camurluk: 0,
    on_tampon: 0, arka_tampon: 0
  };
  const [appraisal, setAppraisal] = useState(initialAppraisal);

  const togglePart = (key) => {
    setAppraisal(prev => ({
      ...prev,
      [key]: (prev[key] + 1) % 4
    }));
  };

  const resetAppraisal = () => {
    setAppraisal(initialAppraisal);
  };

  const getPartStyle = (state) => {
    const base = "p-1.5 md:p-3 text-[10px] leading-tight md:text-xs rounded-xl text-center cursor-pointer transition select-none flex flex-col items-center justify-center min-h-[44px] md:min-h-[50px] border ";
    switch (state) {
      case 1:
        return base + "bg-amber-50 text-amber-900 border-amber-400 hover:bg-amber-100 shadow-sm ring-1 ring-amber-300";
      case 2:
        return base + "bg-orange-100 text-orange-900 border-orange-400 hover:bg-orange-200 shadow-sm font-semibold ring-1 ring-orange-300";
      case 3:
        return base + "bg-red-100 text-red-900 border-red-500 hover:bg-red-200 shadow-sm font-bold ring-1 ring-red-400";
      default:
        return base + "bg-white text-slate-700 border-slate-200 hover:border-blue-400 hover:bg-blue-50/20";
    }
  };

  const getPartBadge = (state) => {
    switch (state) {
      case 1: return <span className="text-[7.5px] md:text-[9px] font-bold px-1 md:px-1.5 py-0.5 rounded bg-amber-200 text-amber-800 mt-0.5">Lokal</span>;
      case 2: return <span className="text-[7.5px] md:text-[9px] font-bold px-1 md:px-1.5 py-0.5 rounded bg-orange-200 text-orange-800 mt-0.5">Boyalı</span>;
      case 3: return <span className="text-[7.5px] md:text-[9px] font-bold px-1 md:px-1.5 py-0.5 rounded bg-red-200 text-red-800 mt-0.5">Değişen</span>;
      default: return <span className="text-[7.5px] md:text-[9px] text-slate-400 mt-0.5">Orijinal</span>;
    }
  };

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
      const cleanFilters = Object.fromEntries(
        Object.entries(currentFilters).filter(([_, v]) => v !== "")
      );
      const res = await fetch('/api/dynamic_options', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleanFilters),
      });
      if (!res.ok) throw new Error("Seçenekler yüklenirken bir hata oluştu.");
      const data = await res.json();
      if (data.status === "success" || data.markalar || data.Marka) {
        const normalizedOptions = {
          Marka: data.Marka || data.markalar || [],
          Seri: data.Seri || data.seriler || [],
          Model: data.Model || data.modeller || [],
          Yil: data.Yil || data.yillar || [],
          Vites_Tipi: data.Vites_Tipi || data.vitesler || [],
          Yakit_Tipi: data.Yakit_Tipi || data.yakitlar || [],
          Kasa_Tipi: data.Kasa_Tipi || data.kasalar || [],
          Renk: data.Renk || data.renkler || [],
          Cekis: data.Cekis || [],
          Motor_Hacmi: data.Motor_Hacmi || [],
          Motor_Gucu: data.Motor_Gucu || [],
          Garanti_Durumu: data.Garanti_Durumu || data.garanti_durumu || [],
          Silindir_Sayisi: data.Silindir_Sayisi || [],
          Koltuk_Sayisi: data.Koltuk_Sayisi || [],
          Kimden: data.Kimden || data.kimden || [],
          Boya_Degisen: data.Boya_Degisen || [],
        };
        setOptions(normalizedOptions);
        
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
            const availableOptions = normalizedOptions[optKey] ? normalizedOptions[optKey].map(String) : [];
            
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
      console.error("API Fetch Error:", err);
      toast.error("Araç seçenekleri yüklenirken hata oluştu.");
    } finally {
      setLoadingOptions(false);
    }
  };

  const handleChange = async (e) => {
    const { name, value } = e.target;
    
    const next = { ...formData, [name]: value };
    
    // Cascading resets
    if (name === "Marka") {
      next.Seri = ""; next.Model = ""; next.Yil = "";
      next.Vites_Tipi = ""; next.Yakit_Tipi = ""; next.Kasa_Tipi = ""; next.Renk = "";
      next.Motor_Hacmi_cc = ""; next.Motor_Gucu_hp = ""; next.Silindir_Sayisi = ""; next.Koltuk_Sayisi = "";
    } else if (name === "Seri") {
      next.Model = ""; next.Yil = "";
      next.Vites_Tipi = ""; next.Yakit_Tipi = ""; next.Kasa_Tipi = ""; next.Renk = "";
      next.Motor_Hacmi_cc = ""; next.Motor_Gucu_hp = ""; next.Silindir_Sayisi = ""; next.Koltuk_Sayisi = "";
    } else if (name === "Model") {
      next.Yil = "";
      next.Vites_Tipi = ""; next.Yakit_Tipi = ""; next.Kasa_Tipi = ""; next.Renk = "";
      next.Motor_Hacmi_cc = ""; next.Motor_Gucu_hp = ""; next.Silindir_Sayisi = ""; next.Koltuk_Sayisi = "";
    }

    // Kullanıcı manuel değiştirirse auto-filled durumunu kaldır
    if (autoFilledFields[name]) {
      setAutoFilledFields(prev => ({ ...prev, [name]: false }));
    }

    // Yıl 4 haneli olarak girildiğinde AI auto-fill yap
    if (name === "Yil" && value && value.length === 4 && next.Marka && next.Seri && next.Model) {
      try {
        const res = await fetch('/api/auto_fill_specs', {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            Marka: next.Marka,
            Seri: next.Seri,
            Model: next.Model
          }),
        });
        if (res.ok) {
          const autoData = await res.json();
          const newAutoFilled = { ...autoFilledFields };
          let changed = false;
          
          Object.keys(autoData).forEach(key => {
            if (autoData[key] !== null && autoData[key] !== undefined) {
              const mappedKey = key === "Motor_Hacmi" ? "Motor_Hacmi_cc" : 
                                key === "Motor_Gucu" ? "Motor_Gucu_hp" : key;
              
              if (next[mappedKey] === "" || next[mappedKey] === "Belirtilmemiş") {
                next[mappedKey] = String(autoData[key]);
                newAutoFilled[mappedKey] = true;
                changed = true;
              }
            }
          });
          
          if (changed) {
            setAutoFilledFields(newAutoFilled);
            toast.success("AI bazı araç özelliklerini otomatik doldurdu ✨", {
              icon: '🤖',
              style: {
                borderRadius: '10px',
                background: '#f0f9ff',
                color: '#0369a1',
              },
            });
          }
        }
      } catch (err) {
        console.error("Auto-fill error:", err);
      }
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
    setResult(null);

    const loaderInterval = setInterval(() => {
      setLoadingMessageIdx(prev => (prev + 1) % loadingMessages.length);
    }, 2000);

    try {
      // Cast numeric fields properly & include 13-part appraisal state
      const payload = {
        ...formData,
        ...appraisal,
        Yil: parseInt(formData.Yil, 10) || 0,
        Kilometre: parseInt(formData.Kilometre, 10) || 0,
        Tramer_TL: parseFloat(formData.Tramer_TL) || 0,
        Motor_Hacmi_cc: formData.Motor_Hacmi_cc ? parseFloat(formData.Motor_Hacmi_cc) : null,
        Motor_Gucu_hp: formData.Motor_Gucu_hp ? parseFloat(formData.Motor_Gucu_hp) : null,
      };

      const res = await fetch('/api/predict', {
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
      toast.error("Sunucuya bağlanılamadı, lütfen tekrar deneyin.");
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

  const handleDownloadPDF = async () => {
    try {
      const toastId = toast.loading('PDF hazırlanıyor...');
      const htmlToImage = await import('html-to-image');
      const { jsPDF } = await import('jspdf');
      
      const element = document.getElementById('pdf-report-container');
      if (!element) return;
      
      const imgData = await htmlToImage.toPng(element, {
        pixelRatio: 2,
        backgroundColor: '#f8fafc', // slate-50
        style: {
          transform: 'scale(1)',
          transformOrigin: 'top left'
        }
      });
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (element.offsetHeight * pdfWidth) / element.offsetWidth;
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Degerinde_Rapor_${formData.Marka}_${formData.Model}.pdf`);
      
      toast.success('PDF başarıyla indirildi!', { id: toastId });
    } catch (error) {
      console.error('PDF generation error:', error);
      toast.error('PDF oluşturulurken bir hata oluştu.');
    }
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
                  {loadingOptions && (!options.Marka || options.Marka.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select required name="Marka" value={formData.Marka} onChange={handleChange} disabled={loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Marka Seçin</option>
                    {options.Marka?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Seri *</label>
                  {loadingOptions && (!options.Seri || options.Seri.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select required name="Seri" value={formData.Seri} onChange={handleChange} disabled={!formData.Marka || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Seri Seçin</option>
                    {options.Seri?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Model / Donanım *</label>
                  {loadingOptions && (!options.Model || options.Model.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select required name="Model" value={formData.Model} onChange={handleChange} disabled={!formData.Seri || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Donanım Seçin</option>
                    {options.Model?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Yıl *</label>
                  {loadingOptions && (!options.Yil || options.Yil.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select required name="Yil" value={formData.Yil} onChange={handleChange} disabled={!formData.Model || loadingOptions} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 appearance-none">
                    <option value="">Yıl Seçin</option>
                    {options.Yil?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
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
                  <label className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center gap-1">Yakıt Tipi {autoFilledFields['Yakit_Tipi'] && <span className="text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded-full font-bold">✨ AI</span>}</label>
                  {loadingOptions && (!options.Yakit_Tipi || options.Yakit_Tipi.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Yakit_Tipi" value={formData.Yakit_Tipi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Yakit_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center gap-1">Vites Tipi {autoFilledFields['Vites_Tipi'] && <span className="text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded-full font-bold">✨ AI</span>}</label>
                  {loadingOptions && (!options.Vites_Tipi || options.Vites_Tipi.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Vites_Tipi" value={formData.Vites_Tipi} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Vites_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Renk</label>
                  {loadingOptions && (!options.Renk || options.Renk.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Renk" value={formData.Renk} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Renk?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
              </div>
            </div>

            <hr className="border-slate-100" />

            {/* Section 3: 13-Part Interactive Car Appraisal */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs">3</span>
                  13 Parçalı Ekspertiz Seçimi
                </h3>
                <button type="button" onClick={resetAppraisal} className="text-xs text-slate-500 hover:text-blue-600 underline font-medium">
                  Tümünü Orijinal Yap
                </button>
              </div>
              
              <p className="text-xs text-slate-500">Parçaya tıklayarak durumu değiştirin: <span className="text-emerald-700 font-semibold">Orijinal</span> → <span className="text-amber-700 font-semibold">Lokal Boya</span> → <span className="text-orange-700 font-semibold">Boyalı</span> → <span className="text-red-700 font-semibold">Değişen</span></p>

              {/* Status Badges Summary */}
              <div className="flex flex-wrap gap-2 text-xs font-semibold py-1">
                <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {Object.values(appraisal).filter(v => v === 0).length} Orijinal
                </span>
                <span className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                  {Object.values(appraisal).filter(v => v === 1).length} Lokal Boya
                </span>
                <span className="px-2.5 py-1 rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                  {Object.values(appraisal).filter(v => v === 2).length} Boyalı
                </span>
                <span className="px-2.5 py-1 rounded-full bg-red-100 text-red-800 border border-red-200">
                  {Object.values(appraisal).filter(v => v === 3).length} Değişen
                </span>
              </div>

              {/* Interactive Car Body Grid */}
              <div className="grid grid-cols-3 gap-1.5 md:gap-2 bg-slate-100 p-2 md:p-3.5 rounded-2xl border border-slate-200 shadow-inner">
                {/* Row 1: Front Bumper */}
                <div className="col-span-1"></div>
                <div onClick={() => togglePart('on_tampon')} className={getPartStyle(appraisal.on_tampon)}>
                  <span className="font-bold">Ön Tampon</span>
                  {getPartBadge(appraisal.on_tampon)}
                </div>
                <div className="col-span-1"></div>

                {/* Row 2: Hood & Front Fenders */}
                <div onClick={() => togglePart('sol_on_camurluk')} className={getPartStyle(appraisal.sol_on_camurluk)}>
                  <span>Sol Ön Çamurluk</span>
                  {getPartBadge(appraisal.sol_on_camurluk)}
                </div>
                <div onClick={() => togglePart('kaput')} className={getPartStyle(appraisal.kaput)}>
                  <span className="font-bold">Motor Kaputu</span>
                  {getPartBadge(appraisal.kaput)}
                </div>
                <div onClick={() => togglePart('sag_on_camurluk')} className={getPartStyle(appraisal.sag_on_camurluk)}>
                  <span>Sağ Ön Çamurluk</span>
                  {getPartBadge(appraisal.sag_on_camurluk)}
                </div>

                {/* Row 3: Front Doors & Roof */}
                <div onClick={() => togglePart('sol_on_kapi')} className={getPartStyle(appraisal.sol_on_kapi)}>
                  <span>Sol Ön Kapı</span>
                  {getPartBadge(appraisal.sol_on_kapi)}
                </div>
                <div onClick={() => togglePart('tavan')} className={getPartStyle(appraisal.tavan)}>
                  <span className="font-bold">Tavan</span>
                  {getPartBadge(appraisal.tavan)}
                </div>
                <div onClick={() => togglePart('sag_on_kapi')} className={getPartStyle(appraisal.sag_on_kapi)}>
                  <span>Sağ Ön Kapı</span>
                  {getPartBadge(appraisal.sag_on_kapi)}
                </div>

                {/* Row 4: Rear Doors */}
                <div onClick={() => togglePart('sol_arka_kapi')} className={getPartStyle(appraisal.sol_arka_kapi)}>
                  <span>Sol Arka Kapı</span>
                  {getPartBadge(appraisal.sol_arka_kapi)}
                </div>
                <div className="bg-slate-200/60 rounded-xl flex flex-col items-center justify-center text-[10px] text-slate-400 font-bold tracking-widest uppercase p-2 border border-slate-300/40">
                  <svg className="w-5 h-5 text-slate-400/60 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h8m-8 4h8m-8 4h8"></path></svg>
                  KABİN
                </div>
                <div onClick={() => togglePart('sag_arka_kapi')} className={getPartStyle(appraisal.sag_arka_kapi)}>
                  <span>Sağ Arka Kapı</span>
                  {getPartBadge(appraisal.sag_arka_kapi)}
                </div>

                {/* Row 5: Rear Fenders & Trunk */}
                <div onClick={() => togglePart('sol_arka_camurluk')} className={getPartStyle(appraisal.sol_arka_camurluk)}>
                  <span>Sol Arka Çamurluk</span>
                  {getPartBadge(appraisal.sol_arka_camurluk)}
                </div>
                <div onClick={() => togglePart('bagaj')} className={getPartStyle(appraisal.bagaj)}>
                  <span className="font-bold">Bagaj Kapağı</span>
                  {getPartBadge(appraisal.bagaj)}
                </div>
                <div onClick={() => togglePart('sag_arka_camurluk')} className={getPartStyle(appraisal.sag_arka_camurluk)}>
                  <span>Sağ Arka Çamurluk</span>
                  {getPartBadge(appraisal.sag_arka_camurluk)}
                </div>

                {/* Row 6: Rear Bumper */}
                <div className="col-span-1"></div>
                <div onClick={() => togglePart('arka_tampon')} className={getPartStyle(appraisal.arka_tampon)}>
                  <span className="font-bold">Arka Tampon</span>
                  {getPartBadge(appraisal.arka_tampon)}
                </div>
                <div className="col-span-1"></div>
              </div>

              {/* Tramer, Kimden, Garanti Durumu */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Tramer Kaydı (TL)</label>
                  <input type="number" name="Tramer_TL" min="0" value={formData.Tramer_TL} onChange={handleChange} placeholder="Örn: 15.000" className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Kimden</label>
                  {loadingOptions && (!options.Kimden || options.Kimden.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Kimden" value={formData.Kimden} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Kimden?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Garanti Durumu</label>
                  {loadingOptions && (!options.Garanti_Durumu || options.Garanti_Durumu.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Garanti_Durumu" value={formData.Garanti_Durumu} onChange={handleChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm outline-none transition">
                    <option value="">Belirtilmemiş</option>
                    {options.Garanti_Durumu?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
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

          {!loadingPredict && result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              <div className="flex justify-end">
                <button onClick={handleDownloadPDF} type="button" className="flex items-center gap-2 bg-blue-50 text-blue-700 hover:bg-blue-100 font-bold py-2.5 px-5 rounded-xl transition duration-200 shadow-sm border border-blue-200">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                  PDF Olarak İndir
                </button>
              </div>

              <div id="pdf-report-container" className="space-y-6 bg-slate-50 rounded-3xl pb-4">
                
                <div className="bg-white p-6 rounded-t-3xl border-b border-slate-200 flex justify-between items-center shadow-sm">
                   <div className="flex items-center gap-2">
                     <svg className="w-8 h-8 text-blue-600" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                       <path d="M15 70 L30 70 L40 45 L70 45 L80 70 L95 70" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
                       <circle cx="30" cy="70" r="7" fill="white" stroke="currentColor" strokeWidth="5"/>
                       <circle cx="80" cy="70" r="7" fill="white" stroke="currentColor" strokeWidth="5"/>
                       <path d="M25 40 L45 20 L60 30 L85 10" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
                       <path d="M70 10 L85 10 L85 25" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
                     </svg>
                     <span className="text-xl tracking-tight">
                       <span className="font-extrabold text-blue-700">Değer</span><span className="font-medium text-slate-500">inde.</span>
                     </span>
                   </div>
                   <div className="text-right">
                     <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Ekspertiz ve Değerleme Raporu</p>
                     <p className="text-sm font-bold text-slate-800">{formData.Marka} {formData.Seri} {formData.Model}</p>
                     <p className="text-xs font-medium text-slate-500 mt-0.5">{formData.Yil} Model • {formatKm(formData.Kilometre)} km</p>
                   </div>
                </div>

              
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
                  {formatMoney(result.tahmini_fiyat ?? result.predicted_price)}
                </h2>
                
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-6 border-t border-slate-100">
                  <div className="text-center sm:text-left w-full sm:w-auto">
                    <p className="text-[10px] md:text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Tahmini Piyasa Fiyat Aralığı</p>
                    <p className="text-base md:text-lg font-bold text-slate-700 bg-slate-50 px-4 py-2 rounded-xl inline-block sm:block">
                      {formatMoney(result.fiyat_araligi?.min ?? result.confidence_low)} <span className="text-slate-300 font-normal mx-1">-</span> {formatMoney(result.fiyat_araligi?.max ?? result.confidence_high)}
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
              {result.fiyat_etkenleri && result.fiyat_etkenleri.length > 0 && (
                <div className="bg-white p-6 rounded-3xl shadow-lg shadow-slate-200/50 border border-slate-100">
                  <h3 className="text-sm font-bold text-slate-800 mb-4 px-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                    Yapay Zeka Analizi
                  </h3>
                  <div className="space-y-3">
                    {result.fiyat_etkenleri.map((etken, idx) => (
                      <div key={idx} className={`flex justify-between items-center p-3 rounded-xl ${etken.yon === 'pozitif' ? 'bg-emerald-50' : 'bg-rose-50'}`}>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${etken.yon === 'pozitif' ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                          <span className={`text-sm font-medium ${etken.yon === 'pozitif' ? 'text-emerald-700' : 'text-rose-700'}`}>{etken.isim}</span>
                        </div>
                        <span className={`font-bold ${etken.yon === 'pozitif' ? 'text-emerald-700' : 'text-rose-700'}`}>
                          {etken.yon === 'pozitif' ? '+' : '-'}{formatMoney(etken.miktar)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Damage Analysis Summary Card */}
              {result.hasar_analizi && (
                <div className="bg-white p-6 rounded-3xl shadow-lg shadow-slate-200/50 border border-slate-100">
                  <h3 className="text-sm font-bold text-slate-800 mb-3 px-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                    Ekspertiz ve Hasar Özeti
                  </h3>
                  <div className="bg-slate-50 p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Tespit Edilen Kaporta Durumu</p>
                      <p className="text-sm font-bold text-slate-800 mt-0.5">{result.hasar_analizi.Boya_Durumu}</p>
                    </div>
                    {result.hasar_analizi.Tramer_TL > 0 && (
                      <div className="bg-rose-100 text-rose-800 text-xs font-semibold px-3 py-1.5 rounded-xl">
                        Tramer: {formatMoney(result.hasar_analizi.Tramer_TL)}
                      </div>
                    )}
                  </div>
                </div>
              )}
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
            </div>
          )}

          {!loadingPredict && !result && (
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
