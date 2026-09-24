import json
import os
import csv
import urllib.parse
import urllib.request
from datetime import datetime, timezone

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

FEATURE_SERVER_URL = "https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer"

LAYER_SPECS = (
    {
        "sourceDataset": "points",
        "layerId": 0,
        "expectedEsriGeometryType": "esriGeometryPoint",
        "geometryFamily": "point",
        "output": "data/pois.geojson",
        "downloadAttachments": True,
    },
    {
        "sourceDataset": "lines",
        "layerId": 1,
        "expectedEsriGeometryType": "esriGeometryPolyline",
        "geometryFamily": "line",
        "output": "data/lines.geojson",
        "downloadAttachments": True,
    },
    {
        "sourceDataset": "polygons",
        "layerId": 2,
        "expectedEsriGeometryType": "esriGeometryPolygon",
        "geometryFamily": "polygon",
        "output": "data/polygons.geojson",
        "downloadAttachments": True,
    },
)

DATA_DIR = "data"
DERIVED_DIR = os.path.join(DATA_DIR, "derived")
LAYERS_METADATA_PATH = os.path.join(DERIVED_DIR, "layers-metadata.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
FONT_PATH = "NotoSansHebrew-Regular.ttf"
FONT_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.oga', '.flac', '.wma', '.opus', '.aiff', '.aif', '.amr', '.m4b')
DOMAIN_FIELDS = ("POI_Type", "POI_Topic", "Collect_Name")
COMMON_ENTITY_FIELDS = (
    "GlobalID",
    "OBJECTID",
    "POI_Name",
    "POI_Type",
    "POI_Topic",
    "POI_Description",
    "Collection_date",
    "Collect_Name",
    "CreationDate",
    "Creator",
    "EditDate",
    "Editor",
)

# Preferred leading field order in the point CSV export.
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


def build_url(base_url, path="", params=None):
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if path else base_url.rstrip('/')
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "POIS-Travel-Science/1.4"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
    if isinstance(data, dict) and data.get("error"):
        error = data["error"]
        raise RuntimeError(f"ArcGIS REST error {error.get('code', '')}: {error.get('message', error)}")
    return data


def layer_url(layer_id):
    return f"{FEATURE_SERVER_URL}/{layer_id}"


def fetch_layer_metadata(spec):
    url = build_url(layer_url(spec["layerId"]), params={"f": "json"})
    metadata = fetch_json(url)
    actual_geometry_type = metadata.get("geometryType")
    expected_geometry_type = spec["expectedEsriGeometryType"]
    if actual_geometry_type != expected_geometry_type:
        raise RuntimeError(
            f"Layer {spec['layerId']} ({spec['sourceDataset']}) geometry type is "
            f"{actual_geometry_type!r}; expected {expected_geometry_type!r}."
        )
    return metadata


def fetch_all_features(spec, metadata):
    """Fetch all features for one ArcGIS sublayer using pagination."""
    all_features = []
    offset = 0
    max_record_count = metadata.get("maxRecordCount") or 1000
    try:
        record_count = max(1, min(int(max_record_count), 2000))
    except (TypeError, ValueError):
        record_count = 1000

    while True:
        url = build_url(
            f"{layer_url(spec['layerId'])}/query",
            params={
                "where": "1=1",
                "outFields": "*",
                "f": "geojson",
                "outSR": 4326,
                "returnGeometry": "true",
                "resultOffset": offset,
                "resultRecordCount": record_count,
            },
        )
        data = fetch_json(url)
        features = data.get("features", [])
        if not isinstance(features, list):
            raise RuntimeError(
                f"Layer {spec['layerId']} returned an invalid GeoJSON feature list at offset {offset}."
            )
        if not features:
            break

        all_features.extend(features)
        exceeded = bool(data.get("properties", {}).get("exceededTransferLimit"))
        if len(features) < record_count and not exceeded:
            break
        offset += len(features)

    return all_features


def download_file(url, save_path):
    req = urllib.request.Request(url, headers={"User-Agent": "POIS-Travel-Science/1.4"})
    with urllib.request.urlopen(req) as response, open(save_path, "wb") as out_file:
        out_file.write(response.read())


def optimize_image(image_path, max_dim=600, quality=45):
    """Compress images and apply EXIF-based orientation correction."""
    if not IMAGE_OPTIMIZE_SUPPORT or not os.path.exists(image_path):
        return
    try:
        with Image.open(image_path) as img:
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
    # Retained for backward-compatible PDF generation. The generated PDF text is English-only.
    if not os.path.exists(FONT_PATH):
        print("Downloading PDF font...")
        try:
            download_file(FONT_URL, FONT_PATH)
        except Exception as e:
            print(f"Error downloading PDF font: {e}")


def fix_hebrew(text):
    # Retained for backward-compatible PDF rendering behavior.
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
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return datetime.max


def format_datetime_str(val):
    """Convert a date value to readable DD/MM/YYYY HH:MM format."""
    dt = parse_to_datetime(val)
    if dt == datetime.max:
        return str(val) if val is not None else ""
    return dt.strftime("%d/%m/%Y %H:%M")


def has_coordinates(value):
    if not isinstance(value, list) or not value:
        return False
    if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
        return True
    return any(has_coordinates(item) for item in value if isinstance(item, list))


def is_empty_feature(feature):
    props = feature.get("properties", {})
    geom = feature.get("geometry") or {}
    if has_coordinates(geom.get("coordinates", [])):
        return False

    for v in props.values():
        if v is not None and str(v).strip() not in ("", "None", "null"):
            return False

    return True


def prepare_features(features, geometry_family):
    """Normalize shared date fields while preserving all source properties and geometry."""
    prepared = []
    for feature in features:
        props = feature.setdefault("properties", {})
        geometry = feature.get("geometry") or {}

        if geometry_family == "point" and geometry.get("type") == "Point":
            coords = geometry.get("coordinates", [])
            if len(coords) >= 2 and all(isinstance(v, (int, float)) for v in coords[:2]):
                props["Longitude"] = coords[0]
                props["Latitude"] = coords[1]

        raw_cdate = get_prop_val(props, "CreationDate") or get_prop_val(props, "Date_Point")
        props["_sort_date"] = parse_to_datetime(raw_cdate)

        for key, val in list(props.items()):
            if key == "_sort_date":
                continue
            if any(d_word in key.lower() for d_word in ["date", "time"]) or key in ["Collection_date", "CreationDate", "EditDate"]:
                if val is not None and str(val).strip() != "":
                    props[key] = format_datetime_str(val)

        if not is_empty_feature(feature):
            prepared.append(feature)

    prepared.sort(key=lambda f: f.get("properties", {}).get("_sort_date", datetime.max))
    for feature in prepared:
        feature.get("properties", {}).pop("_sort_date", None)
    return prepared


def get_object_ids(features):
    ids = []
    for feature in features:
        props = feature.get("properties", {})
        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        if oid is not None:
            ids.append(oid)
    return ids


def get_attachments_map(layer_id, object_ids):
    """Return ArcGIS attachment metadata keyed by parent OBJECTID.

    Attachment metadata is part of the authoritative weekly snapshot. A failed
    query must abort the refresh; silently treating a failure as an empty
    attachment list could otherwise delete valid local media during cleanup.
    """
    attachments_map = {}
    if not object_ids:
        return attachments_map

    chunk_size = 100
    base_url = layer_url(layer_id)
    for i in range(0, len(object_ids), chunk_size):
        chunk_ids = object_ids[i:i + chunk_size]
        url = build_url(
            f"{base_url}/queryAttachments",
            params={"objectIds": ",".join(map(str, chunk_ids)), "f": "json"},
        )
        try:
            data = fetch_json(url)
        except Exception as exc:
            raise RuntimeError(
                f"Could not fetch attachments for layer {layer_id}, "
                f"OBJECTID batch starting at index {i}: {exc}"
            ) from exc

        for group in data.get("attachmentGroups", []):
            pid = group.get("parentObjectId")
            attachments_map[pid] = group.get("attachmentInfos", [])

    return attachments_map


def attachment_storage(spec, oid, att_id, att_name):
    """Return local and web-relative paths for one downloaded media attachment.

    Point media keep the established v1.x root-level naming convention to
    avoid rewriting more than one thousand existing files. New line/polygon
    media live in dataset-specific subdirectories so OBJECTID/attachment IDs
    cannot collide across ArcGIS sublayers.
    """
    safe_name = str(att_name).replace("/", "_").replace("\\", "_")
    filename = f"{oid}_{att_id}_{safe_name}"
    dataset = spec["sourceDataset"]

    if dataset == "points":
        local_path = os.path.join(ATTACHMENTS_DIR, filename)
        relative_path = f"data/attachments/{filename}"
    else:
        dataset_dir = os.path.join(ATTACHMENTS_DIR, dataset)
        os.makedirs(dataset_dir, exist_ok=True)
        local_path = os.path.join(dataset_dir, filename)
        relative_path = f"data/attachments/{dataset}/{filename}"

    return local_path, relative_path


def attach_dataset_media(features, spec, metadata):
    """Synchronize attachment references for one ArcGIS dataset.

    Image and audio attachments are downloaded locally for the static website.
    Other media types (for example video) remain direct public ArcGIS URLs.
    Attachment retrieval/download failures abort the refresh so orphan cleanup
    can never be based on an incomplete ArcGIS response.
    """
    if not spec.get("downloadAttachments"):
        for feature in features:
            feature.setdefault("properties", {})["attachments"] = []
        return

    if metadata.get("hasAttachments") is False:
        for feature in features:
            feature.setdefault("properties", {})["attachments"] = []
        return

    object_ids = get_object_ids(features)
    attachments_info_map = get_attachments_map(spec["layerId"], object_ids)
    attachments_map = {}
    base_url = layer_url(spec["layerId"])

    for oid in object_ids:
        att_list = attachments_info_map.get(oid, [])
        attachments_map[oid] = []
        for att in att_list:
            att_id = att.get("id")
            if att_id is None:
                raise RuntimeError(
                    f"Attachment metadata in {spec['sourceDataset']} layer for "
                    f"OBJECTID {oid} is missing an attachment ID."
                )
            att_name = att.get("name") or f"attachment-{att_id}"
            download_url = f"{base_url}/{oid}/attachments/{att_id}"
            att_name_lower = str(att_name).lower()
            content_type = str(att.get("contentType") or "").lower()
            is_image = att_name_lower.endswith(IMAGE_EXTENSIONS) or content_type.startswith("image/")
            is_audio = att_name_lower.endswith(AUDIO_EXTENSIONS) or content_type.startswith("audio/")

            if is_image or is_audio:
                media_kind = "image" if is_image else "audio"
                local_path, relative_path = attachment_storage(
                    spec, oid, att_id, att_name
                )
                if not os.path.exists(local_path):
                    print(
                        f"Downloading {spec['sourceDataset']} {media_kind}: "
                        f"{os.path.relpath(local_path, DATA_DIR)}..."
                    )
                    try:
                        download_file(download_url, local_path)
                    except Exception as exc:
                        raise RuntimeError(
                            f"Could not download attachment {att_id} for "
                            f"{spec['sourceDataset']} OBJECTID {oid}: {exc}"
                        ) from exc

                if is_image:
                    optimize_image(local_path, max_dim=600, quality=45)
                attachments_map[oid].append(relative_path)
            else:
                print(
                    f"Skipping unsupported media download ({att_name}); "
                    "keeping the direct URL."
                )
                attachments_map[oid].append(download_url)

    for feature in features:
        props = feature.get("properties", {})
        oid = props.get("OBJECTID") or props.get("objectid") or props.get("FID")
        props["attachments"] = attachments_map.get(oid, [])


def local_attachment_references(snapshots):
    """Return normalized repository-relative local attachment references."""
    refs = set()
    for snapshot in snapshots.values():
        for feature in snapshot["features"]:
            attachments = feature.get("properties", {}).get("attachments", [])
            if not isinstance(attachments, list):
                continue
            for ref in attachments:
                if not isinstance(ref, str):
                    continue
                text = ref.strip().replace("\\", "/")
                if not text or text.startswith("http://") or text.startswith("https://"):
                    continue
                refs.add(text)
    return refs


def prune_orphan_attachments(snapshots):
    """Remove local media no longer referenced by the current AGOL snapshot.

    This covers both deleted ArcGIS entities and attachments removed from a
    surviving entity. `.gitkeep` files are retained. GitHub Actions uses
    `git add data/`, so these deletions are staged and committed automatically.
    """
    expected_refs = local_attachment_references(snapshots)
    removed = []

    if not os.path.isdir(ATTACHMENTS_DIR):
        return removed

    for root, _, files in os.walk(ATTACHMENTS_DIR, topdown=False):
        for filename in files:
            if filename == ".gitkeep":
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, ".").replace("\\", "/")
            if rel_path not in expected_refs:
                os.remove(full_path)
                removed.append(rel_path)

        # Remove empty dataset directories while retaining data/attachments.
        if os.path.abspath(root) != os.path.abspath(ATTACHMENTS_DIR):
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except OSError:
                pass

    return removed

def coded_domain_values(field):
    domain = field.get("domain") if isinstance(field, dict) else None
    if not isinstance(domain, dict) or domain.get("type") != "codedValue":
        return []
    values = []
    for item in domain.get("codedValues", []):
        if not isinstance(item, dict):
            continue
        values.append({"code": item.get("code"), "label": item.get("name")})
    return values


def observed_values(features, field_name):
    values = set()
    for feature in features:
        value = get_prop_val(feature.get("properties", {}), field_name)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in ("none", "null"):
            values.add(text)
    return sorted(values, key=str.casefold)


def build_layer_metadata_record(spec, metadata, features):
    fields = metadata.get("fields", []) if isinstance(metadata.get("fields"), list) else []
    fields_by_name = {field.get("name"): field for field in fields if isinstance(field, dict) and field.get("name")}

    domains = {}
    observed = {}
    for field_name in DOMAIN_FIELDS:
        domains[field_name] = coded_domain_values(fields_by_name.get(field_name, {}))
        observed[field_name] = observed_values(features, field_name)

    return {
        "layerId": spec["layerId"],
        "layerName": metadata.get("name"),
        "sourceDataset": spec["sourceDataset"],
        "sourceUrl": layer_url(spec["layerId"]),
        "geometryFamily": spec["geometryFamily"],
        "esriGeometryType": metadata.get("geometryType"),
        "entityCount": len(features),
        "hasAttachments": bool(metadata.get("hasAttachments")),
        "maxRecordCount": metadata.get("maxRecordCount"),
        "objectIdField": metadata.get("objectIdField"),
        "globalIdField": metadata.get("globalIdField"),
        "fieldNames": [field.get("name") for field in fields if isinstance(field, dict) and field.get("name")],
        "commonFieldAvailability": {
            field_name: field_name in fields_by_name for field_name in COMMON_ENTITY_FIELDS
        },
        "domains": domains,
        "observedValues": observed,
    }


def generate_csv(features, output_path):
    print("Generating point CSV...")
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

    print("Generating point PDF...")
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


def write_geojson(features, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"type": "FeatureCollection", "features": features}, handle, ensure_ascii=False, indent=2)


def fetch_and_process():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DERIVED_DIR, exist_ok=True)
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    with open(os.path.join(ATTACHMENTS_DIR, ".gitkeep"), "w", encoding="utf-8") as handle:
        handle.write("")

    # Fetch all three datasets before writing outputs so a failed sublayer cannot
    # silently publish a partially refreshed multi-layer snapshot.
    snapshots = {}
    for index, spec in enumerate(LAYER_SPECS, start=1):
        print(
            f"{index}. Reading {spec['sourceDataset']} layer metadata "
            f"(FeatureServer/{spec['layerId']})..."
        )
        metadata = fetch_layer_metadata(spec)
        print(f"   Fetching {spec['sourceDataset']} features...")
        raw_features = fetch_all_features(spec, metadata)
        features = prepare_features(raw_features, spec["geometryFamily"])
        snapshots[spec["sourceDataset"]] = {
            "spec": spec,
            "metadata": metadata,
            "features": features,
        }
        print(
            f"   Found {len(features)} {spec['sourceDataset']} entities after processing."
        )

    print("4. Synchronizing attachments for points, lines and polygons...")
    for spec in LAYER_SPECS:
        snapshot = snapshots[spec["sourceDataset"]]
        attach_dataset_media(
            snapshot["features"],
            snapshot["spec"],
            snapshot["metadata"],
        )

    point_snapshot = snapshots["points"]

    print("5. Writing multi-layer GeoJSON outputs...")
    for spec in LAYER_SPECS:
        features = snapshots[spec["sourceDataset"]]["features"]
        write_geojson(features, spec["output"])
        print(f"   Wrote {spec['output']} ({len(features)} entities).")

    # Keep the long-standing CSV/PDF exports point-based for backward compatibility.
    point_features = point_snapshot["features"]
    generate_csv(point_features, os.path.join(DATA_DIR, "pois.csv"))
    generate_pdf(point_features, os.path.join(DATA_DIR, "pois.pdf"))

    print("6. Writing harvested ArcGIS layer/domain metadata...")
    metadata_output = {
        "schemaVersion": 1,
        "featureServerUrl": FEATURE_SERVER_URL,
        "datasets": {},
    }
    for spec in LAYER_SPECS:
        snapshot = snapshots[spec["sourceDataset"]]
        metadata_output["datasets"][spec["sourceDataset"]] = build_layer_metadata_record(
            spec, snapshot["metadata"], snapshot["features"]
        )

    with open(LAYERS_METADATA_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata_output, handle, ensure_ascii=False, indent=2)

    print("7. Removing local attachments no longer present in ArcGIS Online...")
    removed_attachments = prune_orphan_attachments(snapshots)
    if removed_attachments:
        print(f"   Removed {len(removed_attachments)} orphan attachment file(s).")
        for path in removed_attachments[:10]:
            print(f"   - {path}")
        if len(removed_attachments) > 10:
            print(f"   ... and {len(removed_attachments) - 10} more.")
    else:
        print("   No orphan local attachments found.")

    print("Multi-layer ArcGIS export completed successfully.")
    print("Image and audio attachments are synchronized for points, lines and polygons.")


if __name__ == "__main__":
    fetch_and_process()
