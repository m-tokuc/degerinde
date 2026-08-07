"""
Değerinde — UI Formatter Helper
Maps raw SHAP values into user-friendly UI structures with localized Turkish tags.
"""

def format_currency(value: float) -> str:
    """Formats a float into Turkish Lira currency format (+/- X.XXX TL)."""
    sign = "+" if value >= 0 else "-"
    abs_value = abs(value)
    return f"{sign}{abs_value:,.0f} TL".replace(",", ".")

def format_prediction_for_ui(prediction_response: dict) -> dict:
    """
    Transforms the raw prediction response (specifically the explanation dictionary)
    into a structured format ready for UI rendering.
    """
    final_price = prediction_response.get("final_price", 0)
    
    # Calculate recommended listing range (± 5%)
    min_price = final_price * 0.95
    max_price = final_price * 1.05
    
    # Dictionary to map internal SHAP keys to UI-friendly Turkish labels
    label_map = {
        "brand_model_impact": "Marka ve Model İtibarı / Donanım",
        "km_impact": "Kilometre Durumu",
        "age_impact": "Araç Yaşı",
        "gear_engine_impact": "Motor ve Şanzıman Özellikleri",
        "damage_impact": "Hasar, Boya ve Tramer Geçmişi",
        "other_impact": "Diğer Özellikler (Renk, Garanti vb.)"
    }
    
    value_adders = []
    value_reducers = []
    
    # Parse through the raw explanation and categorize
    for key, label in label_map.items():
        impact_value = prediction_response.get(key, 0)
        
        # We only care about somewhat significant impacts (e.g., magnitude > 50 TL) to avoid clutter
        if abs(impact_value) < 50:
            continue
            
        formatted_item = {
            "label": label,
            "raw_value": impact_value,
            "display_value": format_currency(impact_value)
        }
        
        if impact_value > 0:
            value_adders.append(formatted_item)
        else:
            value_reducers.append(formatted_item)
            
    # Sort them by absolute impact (highest impact first)
    value_adders.sort(key=lambda x: x["raw_value"], reverse=True)
    value_reducers.sort(key=lambda x: x["raw_value"]) # lowest negative first (largest magnitude)

    return {
        "formatted_price": f"{final_price:,.0f} TL".replace(",", "."),
        "price_range": {
            "min": min_price,
            "max": max_price,
            "formatted_min": f"{min_price:,.0f} TL".replace(",", "."),
            "formatted_max": f"{max_price:,.0f} TL".replace(",", ".")
        },
        "value_adders": value_adders,
        "value_reducers": value_reducers
    }
