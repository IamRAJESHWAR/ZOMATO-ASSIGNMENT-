import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def fetch_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_json_ld(soup: BeautifulSoup) -> list:
    """Extract all JSON-LD blobs from the page."""
    blobs = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string)
            blobs.append(data)
        except Exception:
            continue
    return blobs


def extract_restaurant_meta(ld_blobs: list) -> dict:
    meta = {
        "name": None,
        "location": None,
        "address": None,
        "opening_hours": None,
        "contact": None
    }

    def _read_addr(addr_obj):
        parts = []
        for k in ("streetAddress", "addressLocality", "addressRegion", "addressCountry"):
            v = addr_obj.get(k)
            if v:
                parts.append(v)
        return ", ".join(parts) or None

    for blob in ld_blobs:
        # sometimes it's a list of entries
        entries = blob if isinstance(blob, list) else [blob]
        for ent in entries:
            if ent.get("@type") == "Restaurant":
                meta["name"] = ent.get("name")
                if addr := ent.get("address"):
                    meta["address"] = _read_addr(addr)
                    # location = city,region
                    meta["location"] = ", ".join(filter(None, [addr.get("addressLocality"), addr.get("addressRegion")]))
                meta["opening_hours"] = ent.get("openingHours") or ent.get("openingHoursSpecification")
                meta["contact"] = ent.get("telephone")
    return meta


def extract_menu_items_ld(ld_blobs: list) -> list:
    items = []
    for blob in ld_blobs:
        entries = blob if isinstance(blob, list) else [blob]
        for ent in entries:
            if ent.get("@type") == "MenuItem":
                name = ent.get("name")
                desc = ent.get("description")
                offers = ent.get("offers") or {}
                # price can be direct or nested in priceSpecification
                price = offers.get("price") or (offers.get("priceSpecification") or {}).get("price")
                try:
                    price = float(price)
                except Exception:
                    price = None

                # dietaryCategory gives veg/vegan/diet hints
                diet = ent.get("suitableForDiet", "")
                tags = []
                if "VegetarianDiet" in diet:
                    tags.append("vegetarian")
                if "GlutenFreeDiet" in diet:
                    tags.append("gluten-free")
                if "VeganDiet" in diet:
                    tags.append("vegan")

                items.append({
                    "dish_name": name,
                    "price": price,
                    "description": desc,
                    "tags": tags
                })
    return items


# def fallback_menu_items(soup: BeautifulSoup) -> list:
#     """If JSON-LD has no MenuItem, fall back to regex+DOM heuristics."""
#     items = []
#     # find all text nodes containing a rupee price, e.g. "₹250"
#     for price_tag in soup.find_all(string=re.compile(r"[₹₹]\s*\d+")):
#         parent = price_tag.parent
#         text = price_tag.strip()
#         price_val = int(re.sub(r"[^\d]", "", text))
#         # assume the dish-name is the nearest previous heading tag
#         name_tag = parent.find_previous(re.compile("^h[1-6]$"))
#         desc_tag = parent.find_next("p")
#         name = name_tag.get_text(strip=True) if name_tag else None
#         desc = desc_tag.get_text(strip=True) if desc_tag else None

#         # simple inference of veg/non-veg/spicy
#         tags = []
#         if name and re.search(r"\b(paneer|veg|vegetable|dal)\b", name, re.I):
#             tags.append("vegetarian")
#         if name and re.search(r"\b(chicken|mutton|fish|egg)\b", name, re.I):
#             tags.append("non-vegetarian")
#         if desc and "spicy" in desc.lower():
#             tags.append("spicy")

#         items.append({
#             "dish_name": name,
#             "price": price_val,
#             "description": desc,
#             "tags": tags
#         })
#     return items

# def fallback_menu_items(soup: BeautifulSoup) -> list:
#     """If JSON-LD has no MenuItem, fall back to regex+DOM heuristics."""
#     items = []
#     # More specific price pattern with boundaries and limiting digits
#     price_pattern = re.compile(r"[₹₹]\s*\d{1,6}")  # Limit to 6 digits (reasonable price)
    
#     for price_tag in soup.find_all(string=price_pattern):
#         parent = price_tag.parent
#         text = price_tag.strip()
#         # Extract just the price digits (limit to reasonable segment)
#         price_match = re.search(r"[₹₹]\s*(\d{1,6})", text)
#         if not price_match:
#             continue
            
#         try:
#             price_val = int(price_match.group(1))
#             # Sanity check - prices shouldn't be astronomically high
#             if price_val > 100000:  # Unlikely to have dish > 100k rupees
#                 continue
                
#             # assume the dish-name is the nearest previous heading tag
#             name_tag = parent.find_previous(re.compile("^h[1-6]$"))
#             desc_tag = parent.find_next("p")
#             name = name_tag.get_text(strip=True) if name_tag else None
#             desc = desc_tag.get_text(strip=True) if desc_tag else None

#             # simple inference of veg/non-veg/spicy
#             tags = []
#             if name and re.search(r"\b(paneer|veg|vegetable|dal)\b", name, re.I):
#                 tags.append("vegetarian")
#             if name and re.search(r"\b(chicken|mutton|fish|egg)\b", name, re.I):
#                 tags.append("non-vegetarian")
#             if desc and "spicy" in desc.lower():
#                 tags.append("spicy")

#             items.append({
#                 "dish_name": name,
#                 "price": price_val,
#                 "description": desc,
#                 "tags": tags
#             })
#         except (ValueError, AttributeError):
#             continue
            
#     return items

def fallback_menu_items(soup: BeautifulSoup) -> list:
    """If JSON-LD has no MenuItem, fall back to regex+DOM heuristics."""
    items = []
    # More specific price pattern with boundaries and limiting digits
    price_pattern = re.compile(r"[₹₹]\s*\d{1,6}")  # Limit to 6 digits (reasonable price)
    
    # First, try to find all expanded descriptions in the page
    expanded_descriptions = {}
    for expanded_section in soup.find_all(['div', 'span'], class_=re.compile(r'(full|expanded|complete|detail).*desc')):
        dish_name_tag = expanded_section.find_previous(['h3', 'h4', 'h5', 'strong', 'b'])
        if dish_name_tag:
            dish_name = dish_name_tag.get_text(strip=True)
            expanded_descriptions[dish_name] = expanded_section.get_text(strip=True)
    
    for price_tag in soup.find_all(string=price_pattern):
        parent = price_tag.parent
        text = price_tag.strip()
        # Extract just the price digits (limit to reasonable segment)
        price_match = re.search(r"[₹₹]\s*(\d{1,6})", text)
        if not price_match:
            continue
            
        try:
            price_val = int(price_match.group(1))
            # Sanity check - prices shouldn't be astronomically high
            if price_val > 100000:  # Unlikely to have dish > 100k rupees
                continue
                
            # assume the dish-name is the nearest previous heading tag
            name_tag = parent.find_previous(re.compile("^h[1-6]$|strong|b"))
            if not name_tag:
                # Try broader search if no standard heading found
                name_tag = parent.find_previous(['div', 'span'], class_=re.compile(r'(item|dish).*name|title'))
            
            desc_tag = parent.find_next("p") or parent.find_next(['div', 'span'], class_=re.compile(r'desc|detail'))
            name = name_tag.get_text(strip=True) if name_tag else None
            desc = desc_tag.get_text(strip=True) if desc_tag else None
            
            # Clean description text from "read more" patterns
            if desc:
                # Remove "Read more", "Read More", "more..." and similar patterns
                desc = re.sub(r'\b[Rr]ead\s+[Mm]ore\b|[Mm]ore\.\.\.|\s*\.\.\.$', '', desc).strip()
                
                # If description is truncated or very short, look for a better one
                if desc.endswith('...') or len(desc) < 20:
                    # Check our pre-collected expanded descriptions
                    if name and name in expanded_descriptions:
                        desc = expanded_descriptions[name]
                    else:
                        # Look for expanded content in hidden elements
                        full_desc_tag = soup.find(['div', 'span'], 
                                                 attrs={'data-dish-name': name}) if name else None
                        if full_desc_tag and full_desc_tag.get_text(strip=True):
                            desc = full_desc_tag.get_text(strip=True)
                        else:
                            # Try other common patterns for full descriptions
                            selectors = [
                                f'#{re.sub(r"[^a-zA-Z0-9]", "", name)}-full-desc' if name else None,
                                'div.full-description',
                                'div.expanded-text',
                                'div.description-full'
                            ]
                            for selector in selectors:
                                if selector and (tag := soup.select_one(selector)):
                                    if tag.get_text(strip=True):
                                        desc = tag.get_text(strip=True)
                                        break

            # If we still have truncated text, we might need to drop the ellipsis
            if desc and desc.endswith('...'):
                desc = desc[:-3].strip()

            # simple inference of veg/non-veg/spicy
            tags = []
            if name and re.search(r"\b(paneer|veg|vegetable|dal)\b", name, re.I):
                tags.append("vegetarian")
            if name and re.search(r"\b(chicken|mutton|fish|egg)\b", name, re.I):
                tags.append("non-vegetarian")
            if desc and "spicy" in desc.lower():
                tags.append("spicy")

            items.append({
                "dish_name": name,
                "price": price_val,
                "description": desc,
                "tags": tags
            })
        except (ValueError, AttributeError):
            continue
            
    return items

def build_knowledge_base(url: str) -> list:
    soup = fetch_page(url)
    ld = parse_json_ld(soup)
    meta = extract_restaurant_meta(ld)
    menu = extract_menu_items_ld(ld)
    if not menu:
        menu = fallback_menu_items(soup)

    # normalize into separate records for RAG
    kb = []
    for dish in menu:
        kb.append({
            "restaurant_name": meta["name"],
            "location": meta["location"] or meta["address"],
            "chunk_type": "dish",
            "content": dish
        })

    kb.append({
        "restaurant_name": meta["name"],
        "location": meta["location"] or meta["address"],
        "chunk_type": "meta",
        "content": {
            "introduction": f"{meta['name']} is a restaurant located in {meta['location'] or meta['address']}.",
            "operating_hours": meta["opening_hours"],
            "contact": meta["contact"],
            "address": meta["address"]
        }
    })

    features = {
        "vegetarian_available": any("vegetarian" in d["tags"] for d in menu),
        "gluten_free_available": any("gluten-free" in d["tags"] for d in menu),
        "spicy_dishes_present": any("spicy" in d["tags"] for d in menu),
        "allergen_info_available": False
    }
    kb.append({
        "restaurant_name": meta["name"],
        "location": meta["location"] or meta["address"],
        "chunk_type": "features",
        "content": features
    })

    return kb


def save_to_file(kb: list, url: str):
    import os
    
    # Create restaurant_data directory if it doesn't exist
    os.makedirs("restaurant_data", exist_ok=True)
    
    name = urlparse(url).path.strip("/").replace("/", "_") or "restaurant"
    fn = os.path.join("restaurant_data", f"{name}_kb.json")
    
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"Saved → {fn}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python multi_zomato_generic.py <zomato_restaurant_url>")
        sys.exit(1)

    url = sys.argv[1]
    kb = build_knowledge_base(url)
    save_to_file(kb, url)
