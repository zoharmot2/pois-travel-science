import json
import os
import csv
import urllib.request
from fpdf import FPDF
from bidi.algorithm import get_display

BASE_URL = "https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer/0"
GEOJSON_URL = f"{BASE_URL}/query?where=1%3D1&outFields=*&f=geojson&outSR=4326&returnGeometry=true"
ATTACHMENTS_URL = f"{BASE_URL}/queryAttachments?where=1%3D1&f=json"

DATA_DIR = "data"
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
FONT_PATH = "NotoSansHebrew-Regular.ttf"
FONT_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def download_file(url, save_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(save_path, "wb") as out_file:
        out_file.write(response.read())

def ensure_hebrew_font():
    """הורדת פונט עברי במידה ואינו קיים במערכת"""
    if not os.path.exists(FONT_PATH):
        print("מוריד פונט עברי עבור ה-PDF...")
        download_file(FONT_URL, FONT_PATH)

def fix_hebrew(text):
    """הפיכת טקסט עברי לתצוגה תקינה מימין לשמאל ב-PDF"""
    if text is None:
        return ""
    return get_display(str(text))

def generate_csv(features, output_path):
    """יצירת קובץ CSV עם כל השדות והקישורים לתמונות"""
    print("יוצר קובץ CSV...")
    if not features:
        return

    # איסוף כל מפתחות השדות מכל הנקודות
    all_keys = set()
    for feat in features:
        all_keys.update(feat.get("properties", {}).keys())

    fieldnames = sorted(list(all_keys))
    if "OBJECTID" in fieldnames:
        fieldnames.remove("OBJECTID")
        fieldnames.insert(0, "OBJECTID")

    # utf-8-sig מבטיח פתיחה תקינה של עברית ב-Excel
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for feat in features:
            props = feat.get("properties", {}).copy()
            if isinstance(props.get("attachments"), list):
                props["attachments"] = ", ".join(props["attachments"])
            writer.writerow(props)

def generate_pdf(features, output_path):
    """יצירת קובץ PDF עם עמוד נפרד לכל נקודה"""
    print("יוצר קובץ PDF...")
    ensure_hebrew_font()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("NotoHebrew", "", FONT_PATH, uni=True)

    for feat in features:
        props = feat.get("properties", {})
        pdf.add_page()

        # כותרת העמוד
        pdf.set_font("NotoHebrew", size=18)
        poi_title = props.get("NAME") or props.get("name") or f"נקודה {props.get('OBJECTID', '')}"
        pdf.cell(0, 10, fix_hebrew(f"דוח נקודה: {poi_title}"), ln=True, align="R")
        pdf.ln(5)

        # טבלת מאפיינים
        pdf.set_font("NotoHebrew", size=11)
        for key, val in props.items():
            if key in ["attachments"] or val is None:
                continue
            line_text = f"{key}: {val}"
            pdf.cell(0, 7, fix_hebrew(line_text), ln=True, align="R")

        # הצגת תמונות
        attachments = props.get("attachments", [])
        if attachments:
            pdf.ln(10)
            pdf.set_font("NotoHebrew", size=13)
            pdf.cell(0, 8, fix_hebrew("צילומים ותמונות:"), ln=True, align="R")
            pdf.ln(3)

            for img_path in attachments:
                if os.path.exists(img_path):
                    try:
                        # הוספת התמונה ל-PDF ברוחב מותאם
                        pdf.image(img_path, w=120, x=45)
                        pdf.ln(5)
                    except Exception as e:
                        print(f"שגיאה בהוספת תמונה {img_path} ל-PDF: {e}")

    pdf.output(output_path)

def fetch_and_process():
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    
    print("1. שליפת GeoJSON מ-ArcGIS...")
    geojson_data = fetch_json(GEOJSON_URL)
    
    print("2. שליפת קבצים מצורפים (Attachments)...")
    try:
        attachments_info = fetch_json(ATTACHMENTS_URL)
        attachments_groups = attachments_info.get("attachmentGroups", [])
    except Exception as e:
        print(f"אזהרה: לא ניתן היה לשלוף קבצים מצורפים: {e}")
        attachments_groups = []

    attachments_map = {}
    for group in attachments_groups:
        parent_id = group.get("parentObjectId")
        attachments_map[parent_id] = []
        
        for att in group.get("attachmentInfos", []):
            att_id = att.get("id")
            att_name = att.get("name")
            download_url = f"{BASE_URL}/{parent_id}/attachments/{att_id}"
            
            safe_filename = f"{parent_id}_{att_id}_{att_name}"
            local_path = os.path.join(ATTACHMENTS_DIR, safe_filename)
            relative_path = f"data/attachments/{safe_filename}"
            
            if not os.path.exists(local_path):
                print(f"מוריד קובץ: {safe_filename}...")
                try:
                    download_file(download_url, local_path)
                except Exception as err:
                    print(f"שגיאה בהורדת {download_url}: {err}")
                    continue
            
            attachments_map[parent_id].append(relative_path)

    features = geojson_data.get("features", [])
    for feature in features:
        obj_id = feature.get("properties", {}).get("OBJECTID")
        feature["properties"]["attachments"] = attachments_map.get(obj_id, [])

    # 1. שמירת GeoJSON
    output_geojson = os.path.join(DATA_DIR, "pois.geojson")
    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    # 2. שמירת CSV
    generate_csv(features, os.path.join(DATA_DIR, "pois.csv"))

    # 3. שמירת PDF
    generate_pdf(features, os.path.join(DATA_DIR, "pois.pdf"))

    print("כל הקבצים (GeoJSON, CSV, PDF, Attachments) נוצרו בהצלחה!")

if __name__ == "__main__":
    fetch_and_process()