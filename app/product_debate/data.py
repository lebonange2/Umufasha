"""Product data and known products database."""
from typing import List, Dict, Any


KNOWN_PRODUCTS = [
    {
        "name": "Portable Power Station",
        "functional_attributes": ["battery", "portable", "AC outlet", "USB charging", "solar compatible"],
        "target_user": "consumer",
        "price_band": "$200-500",
        "channel": "Amazon",
        "materials": ["lithium battery", "plastic housing", "electronics"],
        "regulations": ["FCC", "UL"],
        "pain_points": ["heavy", "slow charging", "limited capacity"]
    },
    {
        "name": "Mealworm Protein Powder",
        "functional_attributes": ["protein supplement", "sustainable", "high protein"],
        "target_user": "consumer",
        "price_band": "$30-60",
        "channel": "DTC",
        "materials": ["mealworm", "processing"],
        "regulations": ["FDA", "USDA"],
        "pain_points": ["taste", "acceptance", "price"]
    },
    {
        "name": "Modular Chicken Coop",
        "functional_attributes": ["modular", "expandable", "easy assembly", "predator protection"],
        "target_user": "hobbyist",
        "price_band": "$300-800",
        "channel": "DTC",
        "materials": ["wood", "hardware", "wire mesh"],
        "regulations": [],
        "pain_points": ["assembly time", "durability", "size"]
    },
    {
        "name": "Compact Hydroponic Saffron Rack",
        "functional_attributes": ["hydroponic", "compact", "LED lighting", "automated"],
        "target_user": "hobbyist",
        "price_band": "$150-300",
        "channel": "DTC",
        "materials": ["plastic", "LED lights", "pumps", "electronics"],
        "regulations": ["FCC"],
        "pain_points": ["complexity", "maintenance", "yield"]
    },
    {
        "name": "Smart Water Bottle",
        "functional_attributes": ["hydration tracking", "app connected", "reminder", "temperature display"],
        "target_user": "consumer",
        "price_band": "$40-80",
        "channel": "Amazon",
        "materials": ["stainless steel", "electronics", "sensors"],
        "regulations": ["FCC"],
        "pain_points": ["battery life", "cleaning", "price"]
    },
    {
        "name": "Ergonomic Standing Desk Converter",
        "functional_attributes": ["height adjustable", "keyboard tray", "monitor stand", "cable management"],
        "target_user": "professional",
        "price_band": "$150-300",
        "channel": "Amazon",
        "materials": ["steel", "plastic", "mechanism"],
        "regulations": [],
        "pain_points": ["stability", "weight", "assembly"]
    },
    {
        "name": "Portable Espresso Maker",
        "functional_attributes": ["portable", "manual", "no electricity", "compact"],
        "target_user": "consumer",
        "price_band": "$50-150",
        "channel": "Amazon",
        "materials": ["stainless steel", "silicone", "plastic"],
        "regulations": ["FDA"],
        "pain_points": ["effort required", "consistency", "cleaning"]
    },
    {
        "name": "Indoor Air Quality Monitor",
        "functional_attributes": ["PM2.5 sensor", "CO2 sensor", "app connected", "alerts"],
        "target_user": "consumer",
        "price_band": "$80-200",
        "channel": "Amazon",
        "materials": ["electronics", "sensors", "plastic housing"],
        "regulations": ["FCC"],
        "pain_points": ["accuracy", "calibration", "battery"]
    }
]


def get_products_by_category(category: str) -> List[Dict[str, Any]]:
    """Get products by category.
    
    Args:
        category: Product category
        
    Returns:
        List of products in category
    """
    # Simple category matching - can be enhanced
    category_lower = category.lower()
    
    if "power" in category_lower or "energy" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "power" in p["name"].lower() or "battery" in p.get("functional_attributes", [])]
    elif "food" in category_lower or "nutrition" in category_lower or "protein" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "protein" in p["name"].lower() or "food" in p.get("functional_attributes", [])]
    elif "furniture" in category_lower or "desk" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "desk" in p["name"].lower() or "furniture" in p.get("functional_attributes", [])]
    elif "garden" in category_lower or "plant" in category_lower or "hydroponic" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "hydroponic" in p["name"].lower() or "plant" in p.get("functional_attributes", [])]
    elif "coffee" in category_lower or "beverage" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "coffee" in p["name"].lower() or "espresso" in p["name"].lower()]
    elif "air" in category_lower or "monitor" in category_lower:
        return [p for p in KNOWN_PRODUCTS if "air" in p["name"].lower() or "monitor" in p["name"].lower()]
    else:
        # Return all products if category doesn't match
        return KNOWN_PRODUCTS


def load_products_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load products from CSV file.
    
    CSV format:
    name,functional_attributes,target_user,price_band,channel,materials,regulations,pain_points
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of product dictionaries
    """
    import csv
    products = []
    
    try:
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product = {
                    "name": row.get("name", ""),
                    "functional_attributes": row.get("functional_attributes", "").split(",") if row.get("functional_attributes") else [],
                    "target_user": row.get("target_user", ""),
                    "price_band": row.get("price_band", ""),
                    "channel": row.get("channel", ""),
                    "materials": row.get("materials", "").split(",") if row.get("materials") else [],
                    "regulations": row.get("regulations", "").split(",") if row.get("regulations") else [],
                    "pain_points": row.get("pain_points", "").split(",") if row.get("pain_points") else []
                }
                products.append(product)
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return products

