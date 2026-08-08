import json
import os
import csv
import urllib.request
from datetime import datetime

try:
    from fpdf import FPDF
    from bidi.algorithm import get_display
    PDF_SUPPORT = True
except ImportError as e:
    print(f"אזהרה: ספריות PDF חסרות ({e}). הקובץ PDF לא ייווצר.")
    PDF_SUPPORT = False

try:
    from PIL import Image
    IMAGE_OPTIMIZE_SUPPORT = True
except ImportError:
    print("אזהרה: ספרית Pillow חסרה. התמונות יישמרו בגודלן המקורי.")
    IMAGE_OPTIMIZE_SUPPORT = False

BASE_URL = "https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer/0"
GEOJSON_URL = f"{BASE_URL}/query?where=1%3D1&outFields=*&f=geojson&outSR=4326&returnGeometry=true"

DATA_DIR = "data"
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
FONT_PATH = "NotoSansHebrew-Regular.ttf"
FONT_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def download_file(url, save_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(save_path, "wb") as out_file:
        out_file.write(response.read())

def optimize_image(image_path, max_dim=1000, quality=70):
    if not IMAGE_OPTIMIZE_SUPPORT or not os.path.exists(image_path):
        return
    try:
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            w, h = img.size
            if w > max_dim or h > max_dim:
                if w > h:
                    new_w = max_dim
                    new_h = int(h * (max_dim / w))
                else:
                    new_h = max_dim
                    new_w = int(w * (max_dim / h))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            img.save(image_path, "JPEG", optimize=True, quality=quality)
    except Exception as e:
        print(f"אזהרה: לא ניתן היה לבצע אופטימיזציה לתמונה {image_path}: {e}")

def ensure_hebrew_font():
    if not os.path.exists(FONT_PATH):
        print("מוריד פונט עברי עבור ה-PDF...")
        try:
            download_file(FONT_URL, FONT_PATH)
        except Exception as e:
            print(f"שגיאה בהורדת הפונט: {e}")

def fix_hebrew(text):
    if text is None:
        return ""
    if PDF_SUPPORT:
        try:
            return get_display(str(text))
        except Exception:
            return str(text)
    return str(text)

def get_prop_val(props, key_name):
    if key_name in props and props[key_name] is not None:
        return props[key_name]
    for k, v in props.items():
        if k.lower() == key_name.lower() and v is not None:
            return v
    return ""

def format_datetime_str(val):
    if val is None or str(val).strip() == "":
        return ""
    if isinstance(val, (int, float)):
        try:
            if val > 1e11:
                val = val / 1000.0
            return datetime.fromtimestamp(val).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(val)
    if isinstance(val, str):
        if val.isdigit():
            try:
                ts = float(val)
                if ts > 1e11:
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(val)
    return str(val)

def parse_feature_date(feature):
    props = feature.get("properties", {})
    for key, val in props.items():
        if val is not None and any(d_field in key.lower() for d_field in ["date", "time", "created"]):
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                if val.isdigit():
                    return int(val)
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00")).timestamp()
                except Exception:
                    return val
    return props.get("OBJECTID") or props.get("objectid") or 0

def is_empty_feature(feature):
    """סינון נקודות ריקות"""
    props = feature.get("properties", {})
    name = str(get_prop_val(props, "POI_Name") or get_prop_val(props, "name")).strip()
    topic = str(get_prop_val(props, "POI_Topic")).strip()
    desc = str(get_prop_val(props, "POI_Description")).strip()
    atts = props.get("attachments", [])
    return not name and not topic and not desc and not atts

def get_attachments_map(object_ids):
    attachments_map = {}
    if not object_ids:
        return attachments_map

    url_def = f"{BASE_URL}/queryAttachments?definitionExpression=1%3D1&f=json"
    try:
        data = fetch_json(url_def)
        if "attachmentGroups" in data:
            for group in data.get("attachmentGroups", []):
                pid = group.get("parentObjectId")
                attachments_map[pid] = group.get("attachmentInfos", [])
            return attachments_map
    except Exception as e:
        print(f"ניסיון 1 נכשל: {e}")

    ids_str = ",".join(map(str, object_ids))
    url_ids = f"{BASE_URL}/queryAttachments?objectIds={ids_str}&f=json"
    try:
        data = fetch_json(url_ids)
        if "attachmentGroups" in data:
            for group in data.get("attachmentGroups", []):
                pid = group.get("parentObjectId")
                attachments_map[pid] = group.get("attachmentInfos", [])
            return attachments_map
    except Exception as e:
        print(f"ניסיון 2 נכשל: {e}")

    for oid in object_ids:
        single_url = f"{BASE_URL}/{oid}/attachments?f=json"
        try:
            data = fetch_json(single_url)
            infos = data.get("attachmentInfos", [])
            if infos:
                attachments_map[oid] = infos
        except Exception:
            pass

    return attachments_map

def generate_csv(features, output_path):
    print("יוצר קובץ CSV...")
    if not features:
        return

    all_keys = set()
    for feat in features:
        all_keys.update(feat.get("properties", {}).keys())

    # סדר העמודות המבוקש בראש קובץ ה-CSV
    priority_fields = [
        "OBJECTID",
        "GlobalID",
        "Date_Point",
        "Collect_Name",
        "POI_Name",
        "POI_Topic",
        "POI_Type",
        "POI_Description",
        "Latitude",
        "Longitude",
        "attachments"
    ]

    remaining_fields = sorted([k for k in all_keys if k not in priority_fields])
    fieldnames = priority_fields + remaining_fields

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for feat in features:
            props = feat.get("properties", {}).copy()
            if isinstance(props.get("attachments"), list):
                props["attachments"] = ", ".join(props["attachments"])
            writer.writerow(props)

def generate_pdf(features, output_path):
    if not PDF_SUPPORT:
        print("מדלג על יצירת PDF (חסרות ספריות תומכות).")
        return

    print("יוצר קובץ PDF...")
    ensure_hebrew_font()

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font("NotoHebrew", "", FONT_PATH, uni=True)

        # דף פתיחה
        pdf.add_page()
        pdf.ln(80)
        pdf.set_font("NotoHebrew", size=32)
        pdf.cell(0, 20, fix_hebrew("יומן מסע"), ln=True, align="C")
        pdf.set_font("NotoHebrew", size=14)
        pdf.cell(0, 10, fix_hebrew("דוח מפורט - נקודות עניין ומדיה"), ln=True, align="C")

        # השדות שיוצגו לכל נקודה ב-PDF בסדר המבוקש
        ordered_fields = [
            ("OBJECTID", "OBJECTID:"),
            ("GlobalID", "GlobalID:"),
            ("Date_Point", "Date_Point:"),
            ("Collect_Name", "Collect_Name:"),
            ("POI_Name", "POI_Name:"),
            ("POI_Topic", "POI_Topic:"),
            ("POI_Type", "POI_Type:"),
            ("POI_Description", "POI_Description:"),
            ("Latitude", "Latitude:"),
            ("Longitude", "Longitude:"),
            ("attachments", "attachments:")
        ]

        for feat in features:
            props = feat.get("properties", {})
            pdf.add_page()

            pdf.set_font("NotoHebrew", size=12)
            for key_name, label in ordered_fields:
                val = get_prop_val(props, key_name)
                if isinstance(val, list):
                    val = ", ".join(val)
                if val is not None and str(val).strip() != "":
                    line_text = f"{label} {val}"
                    pdf.set_x(10)  # יישור לשמאל
                    if key_name == "POI_Description":
                        pdf.multi_cell(0, 8, fix_hebrew(line_text), align="L")
                        pdf.ln(2)
                    else:
                        pdf.cell(0, 8, fix_hebrew(line_text), ln=True, align="L")

            attachments = props.get("attachments", [])
            if attachments:
                pdf.ln(5)
                images = []
                media_links = []

                for att in attachments:
                    if isinstance(att, str) and os.path.exists(att) and att.lower().endswith(IMAGE_EXTENSIONS):
                        images.append(att)
                    else:
                        media_links.append(att)

                if images:
                    pdf.set_x(10)
                    pdf.set_font("NotoHebrew", size=13)
                    pdf.cell(0, 8, fix_hebrew("צילומים ותמונות:"), ln=True, align="L")
                    pdf.ln(3)
                    for img_path in images:
                        try:
                            pdf.image(img_path, w=110, x=10)
                            pdf.ln(5)
                        except Exception as img_err:
                            print(f"אזהרה: לא ניתן להוסיף תמונה {img_path} ל-PDF: {img_err}")

                if media_links:
                    pdf.ln(3)
                    pdf.set_x(10)
                    pdf.set_font("NotoHebrew", size=12)
                    pdf.cell(0, 8, fix_hebrew("סרטונים / קבצי מדיה מצורפים:"), ln=True, align="L")
                    pdf.set_font("NotoHebrew", size=10)
                    for link in media_links:
                        pdf.set_x(10)
                        pdf.cell(0, 6, fix_hebrew(f"קישור ישיר: {link}"), ln=True, align="L")

        pdf.output(output_path)
    except Exception as pdf_err:
        print(f"שגיאה בלתי צפויה ביצירת ה-PDF: {pdf_err}")

def fetch_and_process():
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    with open(os.path.join(ATTACHMENTS_DIR, ".gitkeep"), "w") as f:
        f.write("")

    print("1. שליפת GeoJSON מ-ArcGIS...")
    geojson_data = fetch_json(GEOJSON_URL)
    features = geojson_data.get("features", [])

    object_ids = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        
        coords = geom.get("coordinates", []) if geom else []
        if len(coords) >= 2:
            props["Longitude"] = coords[0]
            props["Latitude"] = coords[1]

        raw_date = get_prop_val(props, "Collection_date") or get_prop_val(props, "CreationDate")
        props["Date_Point"] = format_datetime_str(raw_date)

        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        if oid is not None:
            object_ids.append(oid)

    print(f"נמצאו {len(features)} נקודות בשרת.")

    print("2. שליפת קבצים מצורפים (Attachments)...")
    attachments_info_map = get_attachments_map(object_ids)

    attachments_map = {}
    for oid, att_list in attachments_info_map.items():
        attachments_map[oid] = []
        for att in att_list:
            att_id = att.get("id")
            att_name = att.get("name")
            download_url = f"{BASE_URL}/{oid}/attachments/{att_id}"

            is_image = att_name.lower().endswith(IMAGE_EXTENSIONS)

            if is_image:
                safe_filename = f"{oid}_{att_id}_{att_name}"
                local_path = os.path.join(ATTACHMENTS_DIR, safe_filename)
                relative_path = f"data/attachments/{safe_filename}"

                if not os.path.exists(local_path):
                    print(f"מוריד תמונה: {safe_filename}...")
                    try:
                        download_file(download_url, local_path)
                        optimize_image(local_path)
                    except Exception as err:
                        print(f"שגיאה בהורדת {download_url}: {err}")
                        continue

                attachments_map[oid].append(relative_path)
            else:
                print(f"מדלג על הורדת קובץ מדיה ({att_name}), שומר קישור ישיר.")
                attachments_map[oid].append(download_url)

    for feature in features:
        props = feature.get("properties", {})
        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        props["attachments"] = attachments_map.get(oid, [])

    # 3. סינון נקודות ריקות מתוכן
    features = [f for f in features if not is_empty_feature(f)]
    geojson_data["features"] = features
    print(f"לאחר סינון נקודות ריקות נותרו {len(features)} נקודות.")

    # 4. מיון לפי תאריך מהישן לחדש ביותר
    features.sort(key=parse_feature_date)

    output_geojson = os.path.join(DATA_DIR, "pois.geojson")
    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    generate_csv(features, os.path.join(DATA_DIR, "pois.csv"))
    generate_pdf(features, os.path.join(DATA_DIR, "pois.pdf"))

    print("התהליך הסתיים בהצלחה!")

if __name__ == "__main__":
    fetch_and_process()