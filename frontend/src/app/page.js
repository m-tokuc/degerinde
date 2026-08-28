"use client";
import { useState, useEffect } from "react";
import { toast } from 'react-hot-toast';
import { Car, Download, CheckCircle } from 'lucide-react';
import SearchableCombobox from "@/components/SearchableCombobox";
import CarDamageSVG from "@/components/CarDamageSVG";
import { ThemeToggle } from "@/components/ThemeToggle";

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
    "Hasar analizi yapılıyor...",
    "Yapay zeka fiyatlandırıyor..."
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-sans flex flex-col transition-colors duration-200">
      {/* Premium Header with Logo */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 shadow-sm transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-10 h-10 text-blue-600 dark:text-blue-500" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 70 L30 70 L40 45 L70 45 L80 70 L95 70" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="30" cy="70" r="7" fill="currentColor" stroke="currentColor" strokeWidth="5"/>
              <circle cx="80" cy="70" r="7" fill="currentColor" stroke="currentColor" strokeWidth="5"/>
              <path d="M25 40 L45 20 L60 30 L85 10" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M70 10 L85 10 L85 25" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="text-2xl tracking-tight">
              <span className="font-extrabold text-blue-700 dark:text-blue-400">Değer</span><span className="font-medium text-slate-500 dark:text-slate-300">inde.</span>
            </span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 lg:py-12 grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        {/* Left Side: Elaborate Form */}
        <div className="lg:col-span-7 bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-100 dark:border-slate-800 transition-colors duration-200">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">Araç Bilgilerini Girin</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Gelişmiş yapay zeka algoritmamız ile saniyeler içinde aracınızın piyasa değerini hesaplayın.</p>
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
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Marka *</label>
                  {loadingOptions && (!options.Marka || options.Marka.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <SearchableCombobox
                      options={options.Marka}
                      value={formData.Marka}
                      name="Marka"
                      onChange={handleChange}
                      disabled={loadingOptions}
                      placeholder="Marka Seçin"
                      hasLogo={true}
                    />
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Seri *</label>
                  {loadingOptions && (!options.Seri || options.Seri.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <SearchableCombobox
                      options={options.Seri}
                      value={formData.Seri}
                      name="Seri"
                      onChange={handleChange}
                      disabled={!formData.Marka || loadingOptions}
                      placeholder="Seri Seçin"
                      hasLogo={false}
                    />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Model / Donanım *</label>
                  {loadingOptions && (!options.Model || options.Model.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <SearchableCombobox
                      options={options.Model}
                      value={formData.Model}
                      name="Model"
                      onChange={handleChange}
                      disabled={!formData.Seri || loadingOptions}
                      placeholder="Donanım Seçin"
                      hasLogo={false}
                    />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Yıl *</label>
                  {loadingOptions && (!options.Yil || options.Yil.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 animate-pulse rounded-lg"></div>
                  ) : (
                    <SearchableCombobox
                      options={options.Yil}
                      value={formData.Yil}
                      name="Yil"
                      onChange={handleChange}
                      disabled={!formData.Model || loadingOptions}
                      placeholder="Yıl Seçin"
                      hasLogo={false}
                    />
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Kilometre *</label>
                  <input required type="text" inputMode="numeric" name="Kilometre" value={formatKm(formData.Kilometre)} onChange={handleKmChange} placeholder="Örn: 85.000" className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition dark:text-slate-100" />
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
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">Yakıt Tipi {autoFilledFields['Yakit_Tipi'] && <span className="text-[10px] bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded-full font-bold">✨ AI</span>}</label>
                  {loadingOptions && (!options.Yakit_Tipi || options.Yakit_Tipi.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Yakit_Tipi" value={formData.Yakit_Tipi} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 text-sm outline-none transition dark:text-slate-100">
                    <option value="">Belirtilmemiş</option>
                    {options.Yakit_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">Vites Tipi {autoFilledFields['Vites_Tipi'] && <span className="text-[10px] bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded-full font-bold">✨ AI</span>}</label>
                  {loadingOptions && (!options.Vites_Tipi || options.Vites_Tipi.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Vites_Tipi" value={formData.Vites_Tipi} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 text-sm outline-none transition dark:text-slate-100">
                    <option value="">Belirtilmemiş</option>
                    {options.Vites_Tipi?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Renk</label>
                  {loadingOptions ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <SearchableCombobox
                      options={["Beyaz", "Siyah", "Gri", "Gümüş", "Füme", "Kırmızı", "Mavi", "Lacivert", "Sarı", "Yeşil", "Bordo", "Kahverengi", "Diğer"]}
                      value={formData.Renk}
                      name="Renk"
                      onChange={handleChange}
                      disabled={loadingOptions}
                      placeholder="Renk Seçin"
                      hasColor={true}
                    />
                  )}
                </div>
              </div>
            </div>

            <hr className="border-slate-100" />

            {/* Section 3: 13-Part Interactive Car Appraisal */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-blue-600 dark:text-blue-400 text-xs">3</span>
                  13 Parçalı Ekspertiz Seçimi
                </h3>
                <button type="button" onClick={resetAppraisal} className="text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 underline font-medium">
                  Tümünü Orijinal Yap
                </button>
              </div>
              
              <p className="text-xs text-slate-500 dark:text-slate-400">Parçaya tıklayarak durumu değiştirin: <span className="text-emerald-700 dark:text-emerald-400 font-semibold">Orijinal</span> → <span className="text-amber-700 dark:text-amber-400 font-semibold">Lokal Boya</span> → <span className="text-orange-700 dark:text-orange-400 font-semibold">Boyalı</span> → <span className="text-red-700 dark:text-red-400 font-semibold">Değişen</span></p>

              {/* Status Badges Summary */}
              <div className="flex flex-wrap gap-2 text-xs font-semibold py-1">
                <span className="px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50 transition-colors duration-200">
                  {Object.values(appraisal).filter(v => v === 0).length} Orijinal
                </span>
                <span className="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-400 border border-amber-200 dark:border-amber-800/50 transition-colors duration-200">
                  {Object.values(appraisal).filter(v => v === 1).length} Lokal Boya
                </span>
                <span className="px-2.5 py-1 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400 border border-orange-200 dark:border-orange-800/50 transition-colors duration-200">
                  {Object.values(appraisal).filter(v => v === 2).length} Boyalı
                </span>
                <span className="px-2.5 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border border-red-200 dark:border-red-800/50 transition-colors duration-200">
                  {Object.values(appraisal).filter(v => v === 3).length} Değişen
                </span>
              </div>

              {/* Interactive Car Body SVG */}
              <div className="mt-4">
                <CarDamageSVG appraisal={appraisal} onToggle={togglePart} />
              </div>

              {/* Tramer, Kimden, Garanti Durumu */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Tramer Kaydı (TL)</label>
                  <input type="number" name="Tramer_TL" min="0" value={formData.Tramer_TL} onChange={handleChange} placeholder="Örn: 15.000" className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-sm outline-none transition dark:text-slate-100" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Kimden</label>
                  {loadingOptions && (!options.Kimden || options.Kimden.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Kimden" value={formData.Kimden} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-sm outline-none transition dark:text-slate-100">
                    <option value="">Belirtilmemiş</option>
                    {options.Kimden?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Garanti Durumu</label>
                  {loadingOptions && (!options.Garanti_Durumu || options.Garanti_Durumu.length === 0) ? (
                    <div className="w-full h-[46px] bg-slate-200 dark:bg-slate-800 animate-pulse rounded-lg"></div>
                  ) : (
                    <select name="Garanti_Durumu" value={formData.Garanti_Durumu} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-sm outline-none transition dark:text-slate-100">
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
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center border-2 border-slate-100 dark:border-slate-800 rounded-3xl p-6 md:p-10 text-center bg-white dark:bg-slate-900 shadow-xl shadow-slate-200/50 dark:shadow-none transition-colors duration-200">
              <div className="relative w-32 h-32 mb-8 mx-auto flex items-center justify-center overflow-hidden">
                <style>{`
                  @keyframes laser-scan {
                    0% { transform: translateY(-100%); opacity: 0; }
                    10% { opacity: 1; }
                    90% { opacity: 1; }
                    100% { transform: translateY(100%); opacity: 0; }
                  }
                `}</style>
                <Car className="w-24 h-24 text-slate-300 dark:text-slate-700" strokeWidth={1.5} />
                <div className="absolute top-0 left-0 w-full h-1 bg-blue-500 rounded-full shadow-[0_0_20px_6px_rgba(59,130,246,0.8)]"
                     style={{ animation: 'laser-scan 1.5s linear infinite' }}>
                </div>
              </div>
              <h3 className="text-xl md:text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2 transition-all duration-300">
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
                  <Download className="w-5 h-5" />
                  PDF Olarak İndir
                </button>
              </div>

              <div id="pdf-report-container" className="space-y-6 bg-slate-50 dark:bg-slate-950 rounded-3xl pb-4">
                
                {/* Header with Title */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-t-3xl border-b border-slate-200 dark:border-slate-800 flex justify-between items-center shadow-sm transition-colors duration-200">
                   <div className="flex items-center gap-2">
                     <svg className="w-8 h-8 text-blue-600 dark:text-blue-500" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                       <path d="M15 70 L30 70 L40 45 L70 45 L80 70 L95 70" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
                       <circle cx="30" cy="70" r="7" fill="currentColor" stroke="currentColor" strokeWidth="5"/>
                       <circle cx="80" cy="70" r="7" fill="currentColor" stroke="currentColor" strokeWidth="5"/>
                       <path d="M25 40 L45 20 L60 30 L85 10" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
                       <path d="M70 10 L85 10 L85 25" stroke="#0ea5e9" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
                     </svg>
                     <span className="text-xl tracking-tight">
                       <span className="font-extrabold text-blue-700 dark:text-blue-400">Değer</span><span className="font-medium text-slate-500 dark:text-slate-300">inde.</span>
                     </span>
                   </div>
                   <div className="text-right">
                     <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Ekspertiz ve Değerleme Raporu</p>
                     <h2 className="text-sm md:text-lg font-bold text-slate-800 dark:text-slate-100">{formData.Marka} {formData.Seri}</h2>
                     <p className="text-xs font-medium text-slate-500 mt-0.5">{formData.Model} • {formatKm(formData.Kilometre)} km</p>
                   </div>
                </div>
              
              {/* Outlier Warning */}
              {result.is_outlier && (
                <div className="mx-6 bg-amber-50 border border-amber-200 p-4 rounded-2xl flex items-start gap-3 text-amber-800 shadow-sm">
                  <svg className="w-6 h-6 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  <p className="text-sm font-medium">{result.outlier_warning}</p>
                </div>
              )}

              {/* Primary Price Card */}
              <div className="mx-6 bg-white dark:bg-slate-900 p-6 md:p-10 rounded-3xl shadow-sm dark:shadow-none border border-slate-100 dark:border-slate-800 relative overflow-hidden transition-colors duration-200">
                <div className="absolute top-0 left-0 w-full h-1.5 bg-blue-600"></div>
                <div className="text-center">
                  <p className="text-slate-500 dark:text-slate-400 text-xs md:text-sm font-bold uppercase tracking-widest mb-3">Değerinde. Tavsiye Edilen Satış Fiyatı</p>
                  
                  <h2 className="text-5xl md:text-6xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight my-4">
                    {formatMoney(result.tahmini_fiyat ?? result.predicted_price)}
                  </h2>
                </div>
                
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
                  <div className="text-center sm:text-left w-full sm:w-auto">
                    <p className="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">Tahmini Piyasa Aralığı</p>
                    <p className="text-base md:text-xl font-bold text-slate-700 dark:text-slate-300">
                      {formatMoney(result.fiyat_araligi?.min ?? result.confidence_low)} <span className="text-slate-300 dark:text-slate-600 font-normal mx-2">-</span> {formatMoney(result.fiyat_araligi?.max ?? result.confidence_high)}
                    </p>
                  </div>
                  <div className="hidden sm:block h-10 w-px bg-slate-200 dark:bg-slate-800"></div>
                  <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/30 px-4 py-2 rounded-xl border border-emerald-100 dark:border-emerald-800/50">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                    <span className="text-sm font-bold text-emerald-700 dark:text-emerald-400">Yüksek Güvenilirlik</span>
                  </div>
                </div>
              </div>

              {/* Explainable AI Breakdown - Vertical Waterfall Chart */}
              {result.fiyat_etkenleri && result.fiyat_etkenleri.length > 0 && (
                <div className="mx-6 bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                  <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-6 px-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                    Yapay Zeka Fiyat Analizi (Şelale)
                  </h3>
                  
                  {(() => {
                    const base = result.base_fiyat || result.predicted_price;
                    const total = result.tahmini_fiyat || result.predicted_price;
                    let currentVal = base;
                    const wData = [{ name: "Taban Fiyat", val: base, start: 0, end: base, isTotal: true }];
                    
                    result.fiyat_etkenleri.forEach(f => {
                       const v = f.yon === 'pozitif' ? f.miktar : -f.miktar;
                       wData.push({ name: f.isim, val: v, start: currentVal, end: currentVal + v, isTotal: false });
                       currentVal += v;
                    });
                    wData.push({ name: "Nihai Fiyat", val: total, start: 0, end: total, isTotal: true });
                    
                    const maxVal = Math.max(...wData.map(d => Math.max(d.start, d.end)));
                    const minVal = Math.min(...wData.map(d => Math.min(d.start, d.end, 0))); // ensure 0 is included if needed
                    const range = maxVal - minVal || 1;
                    
                    return (
                      <div className="relative h-64 w-full flex px-2 pb-14 pt-8 border-b border-slate-200 dark:border-slate-800">
                        {wData.map((d, i) => {
                          const bottomPct = ((Math.min(d.start, d.end) - minVal) / range) * 100;
                          const heightPct = Math.max(((Math.abs(d.end - d.start)) / range) * 100, 0.5); // Min height for visibility
                          const isPositive = d.val >= 0;
                          
                          // Softer colors
                          let bgClass = "bg-slate-500/90 dark:bg-slate-500"; // Total
                          if (!d.isTotal) {
                            bgClass = isPositive ? "bg-emerald-400/90" : "bg-rose-400/90";
                          }

                          return (
                            <div key={i} className="flex-1 relative h-full group">
                              <div className="absolute w-full flex justify-center" style={{ bottom: `calc(${bottomPct + heightPct}% + 6px)` }}>
                                <span className={`text-[8px] md:text-[10px] font-bold whitespace-nowrap ${d.isTotal ? 'text-slate-600 dark:text-slate-300' : (isPositive ? 'text-emerald-500 dark:text-emerald-400' : 'text-rose-500 dark:text-rose-400')}`}>
                                  {d.isTotal ? formatMoney(Math.abs(d.val)) : (isPositive ? '+' : '-') + formatMoney(Math.abs(d.val))}
                                </span>
                              </div>
                              
                              <div 
                                className={`absolute left-1/2 -translate-x-1/2 w-6 md:w-10 rounded-sm transition-all duration-300 ${bgClass}`}
                                style={{
                                  height: `${heightPct}%`,
                                  bottom: `${bottomPct}%`
                                }}
                              ></div>
                              
                              <div className="absolute -bottom-10 w-full flex justify-center">
                                <span className="text-[8px] md:text-[9px] font-medium text-slate-400 dark:text-slate-500 leading-tight block w-14 md:w-16 text-center px-0.5 break-words">
                                  {d.name}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Combined Damage and Metrics Card */}
              <div className="mx-6 bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-6 px-2 flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                  Ekspertiz ve Model Detayları
                </h3>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                  {/* Hasar Özeti */}
                  {result.hasar_analizi && (
                    <div className="w-full bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl flex flex-col justify-center border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-1">Tespit Edilen Kaporta Durumu</p>
                      <p className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-3">{result.hasar_analizi.Boya_Durumu}</p>
                      {result.hasar_analizi.Tramer_TL > 0 && (
                        <div>
                          <span className="inline-block bg-rose-100/80 text-rose-800 text-xs font-semibold px-3 py-1.5 rounded-xl border border-rose-200">
                            Tramer: {formatMoney(result.hasar_analizi.Tramer_TL)}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl flex flex-col items-center justify-center text-center border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Algoritma</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800 dark:text-slate-200">XGBoost</p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl flex flex-col items-center justify-center text-center border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">R² Skoru</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800 dark:text-slate-200">{result.model_r2 ? (result.model_r2).toFixed(2) : "0.96"}</p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl flex flex-col items-center justify-center text-center border border-slate-100 dark:border-slate-800 transition-colors duration-200">
                    <p className="text-[10px] md:text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Ort. Hata (MAE)</p>
                    <p className="text-xs md:text-sm font-bold text-slate-800 dark:text-slate-200">± {result.mae ? formatMoney(result.mae) : "₺62.852"}</p>
                  </div>
                </div>
              </div>
            </div>
            </div>
          )}

          {!loadingPredict && !result && (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl p-10 text-center bg-white/50 dark:bg-slate-900/50 transition-colors duration-200">
              <div className="w-32 h-32 mb-6 flex items-center justify-center opacity-25 text-slate-600 dark:text-slate-400">
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
              <h3 className="text-xl font-bold text-slate-700 dark:text-slate-300 mb-3">Değerleme Sonucu</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
                Aracınızın markasını, modelini ve tüm özelliklerini seçerek güncel ve doğru piyasa değerini öğrenebilirsiniz.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Corporate Footer */}
      <footer className="mt-auto py-8 text-center text-slate-400 dark:text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col items-center justify-center gap-2">
          <p className="text-sm font-medium">© 2026 Değerinde. Tüm hakları saklıdır.</p>
          <p className="text-xs flex items-center gap-1 opacity-80">
            <svg className="w-3.5 h-3.5 text-blue-500 dark:text-blue-600" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            XGBoost Machine Learning algoritmaları ile desteklenmektedir.
          </p>
        </div>
      </footer>
    </div>
  );
}
