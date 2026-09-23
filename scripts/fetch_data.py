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
    print(f"Warning: PDF libraries are missing ({e}). The PDF file will not be generated.")
    PDF_SUPPORT = False

try:
    from PIL import Image, ImageOps
    IMAGE_OPTIMIZE_SUPPORT = True
except ImportError:
    print("Warning: Pillow is missing. Images will be kept at their original size.")
    IMAGE_OPTIMIZE_SUPPORT = False

BASE_URL = "https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer/0"

DATA_DIR = "data"
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
FONT_PATH = "NotoSansHebrew-Regular.ttf"
FONT_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

# Preferred leading field order in the CSV export
PRIORITY_FIELDS = [
    "OBJECTID",
    "GlobalID",
    "CreationDate",
    "Collect_Name",
    "POI_Name",
    "POI_Topic",
    "POI_Type",
    "POI_Description",
    "Latitude",
    "Longitude",
    "attachments"
]

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def fetch_all_features():
    """Fetch all point features from ArcGIS using pagination."""
    all_features = []
    offset = 0
    record_count = 1000
    while True:
        url = (
            f"{BASE_URL}/query?where=1%3D1&outFields=*&f=geojson&outSR=4326"
            f"&returnGeometry=true&resultOffset={offset}&resultRecordCount={record_count}"
        )
        try:
            data = fetch_json(url)
            features = data.get("features", [])
            if not features:
                break
            all_features.extend(features)
            if len(features) < record_count:
                break
            offset += len(features)
        except Exception as e:
            print(f"Error fetching data at offset {offset}: {e}")
            break
    return all_features

def download_file(url, save_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(save_path, "wb") as out_file:
        out_file.write(response.read())

def optimize_image(image_path, max_dim=600, quality=45):
    """Compress images and apply EXIF-based orientation correction."""
    if not IMAGE_OPTIMIZE_SUPPORT or not os.path.exists(image_path):
        return
    try:
        with Image.open(image_path) as img:
            # Apply the camera EXIF orientation before saving the image.
            img = ImageOps.exif_transpose(img)

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
        print(f"Warning: could not optimize/orient image {image_path}: {e}")

def ensure_hebrew_font():
    if not os.path.exists(FONT_PATH):
        print("Downloading PDF font...")
        try:
            download_file(FONT_URL, FONT_PATH)
        except Exception as e:
            print(f"Error downloading PDF font: {e}")

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

def parse_to_datetime(val):
    if val is None or str(val).strip() in ("", "None", "null"):
        return datetime.max
    
    if isinstance(val, (int, float)):
        ts = val / 1000.0 if val > 2.5e9 else val
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return datetime.max
            
    val_str = str(val).strip()
    if val_str.isdigit():
        ts = float(val_str)
        ts = ts / 1000.0 if ts > 2.5e9 else ts
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return datetime.max

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(val_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.max

def format_datetime_str(val):
    """Convert a date value to readable DD/MM/YYYY HH:MM format."""
    dt = parse_to_datetime(val)
    if dt == datetime.max:
        return str(val) if val is not None else ""
    return dt.strftime("%d/%m/%Y %H:%M")

def is_empty_feature(feature):
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", []) if geom else []
    
    if coords and len(coords) >= 2:
        return False

    for v in props.values():
        if v is not None and str(v).strip() not in ("", "None", "null"):
            return False

    return True

def get_attachments_map(object_ids):
    attachments_map = {}
    if not object_ids:
        return attachments_map

    chunk_size = 100
    for i in range(0, len(object_ids), chunk_size):
        chunk_ids = object_ids[i:i + chunk_size]
        ids_str = ",".join(map(str, chunk_ids))
        url_ids = f"{BASE_URL}/queryAttachments?objectIds={ids_str}&f=json"
        try:
            data = fetch_json(url_ids)
            if "attachmentGroups" in data:
                for group in data.get("attachmentGroups", []):
                    pid = group.get("parentObjectId")
                    attachments_map[pid] = group.get("attachmentInfos", [])
        except Exception as e:
            print(f"Error fetching attachments for batch {i}: {e}")

    return attachments_map

def generate_csv(features, output_path):
    print("Generating CSV...")
    if not features:
        return

    all_keys = set()
    for feat in features:
        all_keys.update(feat.get("properties", {}).keys())

    remaining_fields = sorted([k for k in all_keys if k not in PRIORITY_FIELDS])
    fieldnames = PRIORITY_FIELDS + remaining_fields

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
        print("Skipping PDF generation because supporting libraries are missing.")
        return

    print("Generating PDF...")
    ensure_hebrew_font()

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        try:
            pdf.add_font("NotoHebrew", fname=FONT_PATH)
        except TypeError:
            pdf.add_font("NotoHebrew", "", FONT_PATH, uni=True)

        pdf.add_page()
        pdf.ln(80)
        pdf.set_font("NotoHebrew", size=32)
        pdf.cell(0, 20, fix_hebrew("Travel Journal"), ln=True, align="C")
        pdf.set_font("NotoHebrew", size=14)
        pdf.cell(0, 10, fix_hebrew("Detailed Report - Points of Interest and Media"), ln=True, align="C")

        for feat in features:
            props = feat.get("properties", {})
            pdf.add_page()

            pdf.set_font("NotoHebrew", size=11)
            
            for key in PRIORITY_FIELDS:
                val = get_prop_val(props, key)
                if isinstance(val, list):
                    val_str = ", ".join([str(x) for x in val])
                else:
                    val_str = "" if val is None else str(val)

                line_text = f"{key}: {val_str}"
                
                pdf.set_x(10)
                pdf.multi_cell(0, 7, fix_hebrew(line_text), align="L")
                pdf.ln(1)

            attachments = props.get("attachments", [])
            if attachments:
                images = [att for att in attachments if isinstance(att, str) and os.path.exists(att) and att.lower().endswith(IMAGE_EXTENSIONS)]
                if images:
                    pdf.ln(4)
                    pdf.set_x(10)
                    pdf.set_font("NotoHebrew", size=12)
                    pdf.cell(0, 8, fix_hebrew("Attached images:"), ln=True, align="L")
                    pdf.ln(2)
                    for img_path in images:
                        try:
                            pdf.image(img_path, w=110, x=10)
                            pdf.ln(4)
                        except Exception as img_err:
                            print(f"Warning: could not add image {img_path} to PDF: {img_err}")

        pdf.output(output_path)
    except Exception as pdf_err:
        print(f"Error generating PDF: {pdf_err}")

def fetch_and_process():
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    with open(os.path.join(ATTACHMENTS_DIR, ".gitkeep"), "w") as f:
        f.write("")

    print("1. Fetching GeoJSON from ArcGIS...")
    features = fetch_all_features()

    object_ids = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        
        coords = geom.get("coordinates", []) if geom else []
        if len(coords) >= 2:
            props["Longitude"] = coords[0]
            props["Latitude"] = coords[1]

        # Preserve the original date value for accurate sorting.
        raw_cdate = get_prop_val(props, "CreationDate") or get_prop_val(props, "Date_Point")
        props["_sort_date"] = parse_to_datetime(raw_cdate)

        # Convert date/time fields to a readable format.
        for key, val in list(props.items()):
            if any(d_word in key.lower() for d_word in ["date", "time"]) or key in ["Collection_date", "CreationDate", "EditDate"]:
                if val is not None and str(val).strip() != "":
                    props[key] = format_datetime_str(val)

        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        if oid is not None:
            object_ids.append(oid)

    print(f"Found {len(features)} point features on the server.")

    print("2. Fetching attachments...")
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
                    print(f"Downloading image: {safe_filename}...")
                    try:
                        download_file(download_url, local_path)
                    except Exception as err:
                        print(f"Error downloading {download_url}: {err}")
                        continue

                # Always optimize and apply EXIF orientation, including previously downloaded files.
                optimize_image(local_path, max_dim=600, quality=45)
                attachments_map[oid].append(relative_path)
            else:
                print(f"Skipping non-image media download ({att_name}); keeping the direct URL.")
                attachments_map[oid].append(download_url)

    for feature in features:
        props = feature.get("properties", {})
        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        props["attachments"] = attachments_map.get(oid, [])

    features = [f for f in features if not is_empty_feature(f)]

    # Sort chronologically by CreationDate, oldest to newest.
    features.sort(key=lambda f: f.get("properties", {}).get("_sort_date", datetime.max))

    # Remove the temporary sort helper field.
    for f in features:
        f.get("properties", {}).pop("_sort_date", None)

    geojson_data = {"type": "FeatureCollection", "features": features}
    print(f"After processing and sorting by CreationDate, {len(features)} point features remain in chronological order (oldest to newest).")

    output_geojson = os.path.join(DATA_DIR, "pois.geojson")
    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    generate_csv(features, os.path.join(DATA_DIR, "pois.csv"))
    generate_pdf(features, os.path.join(DATA_DIR, "pois.pdf"))

    print("Process completed successfully!")

if __name__ == "__main__":
    fetch_and_process()