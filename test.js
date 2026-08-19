const data = {
  "markalar": ["Renault"],
  "seriler": ["Clio"],
  "modeller": ["Touch"],
  "yillar": [2018],
  "vitesler": ["Manuel"],
  "yakitlar": ["Dizel"],
  "kasalar": ["Hatchback 5 Kapı"]
};

let next = {};
let changed = false;

const normalizedOptions = {
  Marka: data.Marka || data.markalar || [],
  Seri: data.Seri || data.seriler || [],
  Model: data.Model || data.modeller || [],
  Yil: data.Yil || data.yillar || [],
  Vites_Tipi: data.Vites_Tipi || data.vitesler || [],
  Yakit_Tipi: data.Yakit_Tipi || data.yakitlar || [],
  Kasa_Tipi: data.Kasa_Tipi || data.kasalar || [],
  Renk: data.Renk || [],
  Cekis: data.Cekis || [],
  Motor_Hacmi: data.Motor_Hacmi || [],
  Motor_Gucu: data.Motor_Gucu || [],
  Garanti_Durumu: data.Garanti_Durumu || [],
  Silindir_Sayisi: data.Silindir_Sayisi || [],
  Koltuk_Sayisi: data.Koltuk_Sayisi || [],
  Kimden: data.Kimden || [],
  Boya_Degisen: data.Boya_Degisen || [],
};

const fieldMap = {
  Marka: "Marka", Seri: "Seri", Model: "Model", Yil: "Yil",
  Vites_Tipi: "Vites_Tipi", Yakit_Tipi: "Yakit_Tipi", Kasa_Tipi: "Kasa_Tipi",
  Renk: "Renk", Cekis: "Cekis", Motor_Hacmi: "Motor_Hacmi_cc",
  Motor_Gucu: "Motor_Gucu_hp", Garanti_Durumu: "Garanti_Durumu",
  Silindir_Sayisi: "Silindir_Sayisi", Koltuk_Sayisi: "Koltuk_Sayisi", Kimden: "Kimden"
};

try {
  Object.keys(fieldMap).forEach(optKey => {
    const formKey = fieldMap[optKey];
    const availableOptions = normalizedOptions[optKey] ? normalizedOptions[optKey].map(String) : [];
    
    if (next[formKey] && next[formKey] !== "" && next[formKey] !== "Belirsiz" && next[formKey] !== "Belirtilmemiş") {
      if (availableOptions.length > 0 && !availableOptions.includes(next[formKey].toString())) {
        next[formKey] = "";
        changed = true;
      }
    }
    
    if (availableOptions.length === 1) {
      const singleVal = availableOptions[0];
      if (next[formKey] !== singleVal) {
        next[formKey] = singleVal;
        changed = true;
      }
    }
  });
  console.log("Success!", next);
} catch (e) {
  console.log("Error:", e);
}
