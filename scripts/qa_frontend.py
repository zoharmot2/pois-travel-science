#!/usr/bin/env python3
"""Static regression QA for the standalone and embedded website shells.

This intentionally avoids browser/network dependencies. It verifies the source-level
contracts that make both display modes and the current v1.2/v1.3 foundation features
possible. Full visual/browser regression remains a manual release gate.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Issue:
    severity: str
    code: str
    message: str


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_attrs = {}
        self.ids = set()
        self.scripts = []
        self.stylesheets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_attrs = attrs
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "script" and attrs.get("src"):
            self.scripts.append((attrs.get("src"), attrs.get("type", "")))
        if tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href"):
            self.stylesheets.append(attrs["href"])


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (ROOT / path).is_file()


def main() -> int:
    issues: list[Issue] = []

    def error(code: str, message: str) -> None:
        issues.append(Issue("ERROR", code, message))

    def warning(code: str, message: str) -> None:
        issues.append(Issue("WARNING", code, message))

    required_files = [
        "index.html", "config.json", "VERSION", "css/app.css",
        "js/app.js", "js/data.js", "js/details.js", "js/embed.js",
        "js/entities.js", "js/filters.js", "js/map.js", "js/metadata.js",
        "data/site/poi-meta.json", "scripts/fetch_data.py", "scripts/qa_data.py", "scripts/qa_config.json"
    ]
    for path in required_files:
        if not exists(path):
            error("REQUIRED_FILE_MISSING", f"Required frontend/foundation file is missing: {path}")

    if any(i.severity == "ERROR" for i in issues):
        return finish(issues)

    html = read("index.html")
    css = read("css/app.css")
    app = read("js/app.js")
    data_js = read("js/data.js")
    details = read("js/details.js")
    embed = read("js/embed.js")
    entities = read("js/entities.js")
    filters = read("js/filters.js")
    map_js = read("js/map.js")
    metadata = read("js/metadata.js")

    parser = PageParser()
    parser.feed(html)

    # English-only authored UI contract.
    if parser.html_attrs.get("lang") != "en":
        error("HTML_LANGUAGE", 'index.html must declare <html lang="en">.')
    if parser.html_attrs.get("dir") != "ltr":
        error("HTML_DIRECTION", 'index.html must declare dir="ltr".')

    hebrew_re = re.compile(r"[\u0590-\u05FF]")
    for path, text in [
        ("index.html", html), ("js/app.js", app), ("js/data.js", data_js),
        ("js/details.js", details), ("js/embed.js", embed),
        ("js/entities.js", entities), ("js/filters.js", filters),
        ("js/map.js", map_js), ("js/metadata.js", metadata)
    ]:
        if hebrew_re.search(text):
            error("NON_ENGLISH_UI_SOURCE", f"Hebrew characters found in authored frontend source: {path}")

    # Core shell and modular frontend.
    for element_id in ["appWorkspace", "map", "poiCount", "entityDetailPanel", "entityDetailTitle", "entityDetailContent", "entityDetailClose"]:
        if element_id not in parser.ids:
            error("HTML_CONTRACT", f"Required element #{element_id} is missing from index.html.")

    if "css/app.css" not in parser.stylesheets:
        error("CSS_ENTRYPOINT", "index.html must load css/app.css.")
    if ("js/app.js", "module") not in parser.scripts:
        error("JS_ENTRYPOINT", 'index.html must load js/app.js with type="module".')

    # External library wiring retained from v1.2.
    for token, label in [
        ("leaflet@1.9.4/dist/leaflet.css", "Leaflet CSS"),
        ("leaflet@1.9.4/dist/leaflet.js", "Leaflet JS"),
        ("leaflet.terminator", "Leaflet Terminator")
    ]:
        if token not in html:
            error("EXTERNAL_LIBRARY", f"{label} reference is missing from index.html.")

    # Standalone / embed contracts.
    if "applyEmbedMode();" not in app:
        error("EMBED_INIT", "app.js must initialize embed mode before creating the map.")
    embed_tokens = ["URLSearchParams", "get('embed')", "embedValue === 'true'", "embedValue === '1'", "embed-mode"]
    for token in embed_tokens:
        if token not in embed:
            error("EMBED_LOGIC", f"embed.js is missing expected embed behavior: {token}")
    if not re.search(r"body\.embed-mode\s+header\s*\{[^}]*display\s*:\s*none", css, re.S):
        error("EMBED_HEADER", "Embedded mode must hide the standalone header in CSS.")
    if "header" not in html or "Points of Interest (POI) Map" not in html:
        error("STANDALONE_HEADER", "Standalone header/title is missing.")

    # Detail panel desktop/embed/mobile contracts.
    for token in [".entity-detail-panel", ".entity-detail-panel.open", "body.embed-mode .entity-detail-panel", "@media (max-width: 700px)"]:
        if token not in css:
            error("DETAIL_PANEL_LAYOUT", f"Detail-panel responsive/embed CSS contract missing: {token}")
    for token in ["POI Details", "Research Topic", "POI Type", "Coordinates", "Technical details", "Attachments"]:
        if token not in html + details:
            error("DETAIL_PANEL_CONTENT", f"Expected English detail-panel label missing: {token}")
    if "Escape" not in details:
        error("DETAIL_PANEL_KEYBOARD", "Detail panel must support Escape-to-close.")

    # Current v1.2 map features that must survive the v1.3 foundation work.
    basemap_tokens = [
        "OpenStreetMap", "Satellite (Esri World Imagery)", "Topographic (Esri Topo)",
        "Light (Esri Light Gray)", "Historic (NatGeo/Esri)"
    ]
    for token in basemap_tokens:
        if token not in map_js:
            error("BASEMAP_REGRESSION", f"Expected basemap missing: {token}")
    control_sources = filters + map_js
    for token in ["Search POI by name...", "Day/Night", "Time Zones", "coordsDisplay", "L.terminator"]:
        if token not in control_sources:
            error("MAP_CONTROL_REGRESSION", f"Expected map utility/control missing: {token}")
    if "SEARCH_DELAY_MS = 180" not in map_js or "findBestMatchingLayer" not in map_js:
        error("SEARCH_REGRESSION", "Optimized debounced single-result search contract is missing.")

    # v1.4 Stage 5 integrated controls: Type legend only, then Search, Geometry, Utilities.
    for token in ["POI Types", "Search", "Geometry", "Map Utilities", "addMapControlPanel", "createGeometryFilterItems", "filterEntitiesByTypeAndGeometry"]:
        if token not in filters + app:
            error("V14_UI_CONTRACT", f"v1.4 integrated map-control contract missing: {token}")
    if "createTopicFilterItems" in app or "activeTopicsState" in app:
        error("TOPIC_LEGEND_REMOVAL", "Research Topic must not remain an active primary legend/filter in app.js.")
    if "extraValues" not in filters or "getTypeFilterValue(entity)" not in filters:
        error("TYPE_EXTENSIBILITY", "POI Type legend must include live values not yet configured.")
    if "unconfiguredTypes" not in app or "default style" not in app.lower():
        error("TYPE_FALLBACK", "Unconfigured POI Types must remain visible with a default style and warning.")
    for family in ["point", "line", "polygon"]:
        if family not in filters:
            error("GEOMETRY_CONTROL", f"Geometry control is missing supported family: {family}")
    order_tokens = ["'POI Types'", "'Search'", "'Geometry'", "'Map Utilities'"]
    positions = [filters.find(token) for token in order_tokens]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        error("CONTROL_ORDER", "Map controls must be ordered POI Types → Search → Geometry → Map Utilities.")
    for token in [".map-ui-panel", ".type-color-swatch", ".geometry-icon", ".map-search-input", ".map-utility-buttons"]:
        if token not in css:
            error("V14_UI_STYLE", f"v1.4 map-control styling contract missing: {token}")
    if "map-ui-panel-collapse" not in filters or "@media (max-width: 700px)" not in css:
        error("V14_UI_RESPONSIVE", "Compact/mobile map-control collapse contract is incomplete.")
    try:
        site_config = json.loads(read("config.json"))
        symbology = site_config.get("symbology", {})
        if symbology.get("field") != "POI_Type":
            error("TYPE_SYMBOLOGY_FIELD", "config.json symbology.field must be POI_Type for v1.4.")
        if not isinstance(symbology.get("types"), dict):
            error("TYPE_SYMBOLOGY_CONFIG", "config.json symbology.types must be an object.")
        default_symbology = symbology.get("default", {})
        for family in ["point", "line", "polygon"]:
            if not isinstance(default_symbology.get(family), dict):
                error("GEOMETRY_SYMBOLOGY_DEFAULT", f"Default {family} symbology settings are missing.")
    except Exception as exc:
        error("SYMBOL_CONFIG_JSON", f"Unable to validate config.json symbology: {exc}")

    # Entity, stable ID, metadata sidecar, future geometry readiness.
    for token in ["GlobalID", "entityId", "geometryFamily", "representativePoint", "sourceDataset"]:
        if token not in entities:
            error("ENTITY_MODEL", f"Entity model contract missing: {token}")
    if "normalizeGlobalId" not in entities or "createEntityIdIndex" not in entities:
        error("STABLE_ID", "Stable GlobalID normalization/indexing contract is missing.")
    if "SITE_METADATA_PATH" not in data_js or "attachSiteMetadata" not in data_js or "websiteMetadata" not in metadata + entities:
        error("METADATA_SIDECAR", "Metadata-sidecar linkage contract is incomplete.")
    for token in ["LineString", "MultiLineString", "Polygon", "MultiPolygon"]:
        if token not in entities:
            error("MULTI_GEOMETRY", f"Future geometry family support missing from Entity model: {token}")
    if "focusMapOnLayer" not in map_js or "getBounds" not in map_js:
        error("MULTI_GEOMETRY_NAVIGATION", "Geometry-aware map focus contract is missing.")

    # v1.4 Stage 6 ArcGIS multi-layer export contract.
    fetch_script = read("scripts/fetch_data.py")
    for token in [
        "POI_Feature_Layer_view/FeatureServer",
        '"sourceDataset": "points"', '"layerId": 0', '"output": "data/pois.geojson"',
        '"sourceDataset": "lines"', '"layerId": 1', '"output": "data/lines.geojson"',
        '"sourceDataset": "polygons"', '"layerId": 2', '"output": "data/polygons.geojson"',
        "layers-metadata.json", "POI_Type", "POI_Topic", "Collect_Name"
    ]:
        if token not in fetch_script:
            error("MULTI_LAYER_EXPORT", f"Stage 6 ArcGIS export contract missing: {token}")
    try:
        qa_config = json.loads(read("scripts/qa_config.json"))
        dataset_specs = {item.get("name"): item for item in qa_config.get("datasets", [])}
        for name in ["points", "lines", "polygons"]:
            if not dataset_specs.get(name, {}).get("required"):
                error("MULTI_LAYER_QA_REQUIRED", f"QA dataset {name} must be required after Stage 6 export activation.")
        required_outputs = set(qa_config.get("requiredFiles", []))
        for output in ["data/pois.geojson", "data/lines.geojson", "data/polygons.geojson", "data/derived/layers-metadata.json"]:
            if output not in required_outputs:
                error("MULTI_LAYER_QA_OUTPUT", f"QA requiredFiles is missing Stage 6 output: {output}")
    except Exception as exc:
        error("MULTI_LAYER_QA_CONFIG", f"Unable to validate Stage 6 QA configuration: {exc}")


    # v1.4 Stage 7 live multi-geometry rendering contract.
    for token in [
        "{ sourceDataset: 'points', path: 'data/pois.geojson', required: true }",
        "{ sourceDataset: 'lines', path: 'data/lines.geojson', required: true }",
        "{ sourceDataset: 'polygons', path: 'data/polygons.geojson', required: true }"
    ]:
        if token not in data_js:
            error("MULTI_GEOMETRY_DATA_SOURCE", f"Active Stage 7 data source missing: {token}")
    for token in ["createPane('polygonPane')", "createPane('linePane')", "polygonPane.style.zIndex", "linePane.style.zIndex"]:
        if token not in map_js:
            error("MULTI_GEOMETRY_PANES", f"Stage 7 geometry pane contract missing: {token}")
    for token in ["pane: 'polygonPane'", "pane: 'linePane'"]:
        if token not in entities:
            error("MULTI_GEOMETRY_STYLE", f"Stage 7 vector style pane contract missing: {token}")

    # v1.4 Stage 8 unified Type + Geometry filtering refinement.
    for token in [
        "UNSPECIFIED_TYPE_VALUE", "getTypeFilterValue", "computeFilterFacets",
        "updateFilterSummary", "Showing ${filteredCount} of ${totalCount} entities"
    ]:
        if token not in filters + app:
            error("UNIFIED_FILTER_REFINEMENT", f"Stage 8 unified filter contract missing: {token}")
    if filters.count("includeAllNone: true") < 2:
        error("FILTER_ALL_NONE", "Both POI Type and Geometry controls must provide All/None actions.")
    for token in [".map-ui-panel-summary", ".control-toggle-item.no-matches", ".synthetic-value"]:
        if token not in css:
            error("FILTER_REFINEMENT_STYLE", f"Stage 8 filter-refinement styling missing: {token}")
    if "!item.synthetic" not in app:
        error("UNSPECIFIED_TYPE_WARNING", "UI-only Unspecified POI Type must not be treated as an unconfigured ArcGIS Type.")


    # v1.4 Stage 9 multi-geometry search + Detail Panel refinement.
    for token in [
        "SEARCH_RESULT_LIMIT = 8", "collectSearchMatches", "map-search-results",
        "ArrowDown", "ArrowUp", "No matching visible entities.", "onSelectEntity"
    ]:
        if token not in map_js + app + css:
            error("MULTI_GEOMETRY_SEARCH", f"Stage 9 search contract missing: {token}")
    for token in [
        ".map-search-result", ".map-search-result-geometry", ".geometry-point",
        ".geometry-line", ".geometry-polygon"
    ]:
        if token not in css:
            error("MULTI_GEOMETRY_SEARCH_STYLE", f"Stage 9 search-result styling missing: {token}")
    for token in [
        "getEntityDisplayName", "Unnamed ${geometryDisplayLabel(entity)}",
        "Map Center (derived)", "Extent", "Source Dataset", "GeoJSON Geometry",
        "entity-detail-audio-item", "<audio controls", "Open audio file"
    ]:
        if token not in details + css:
            error("DETAIL_PANEL_REFINEMENT", f"Stage 9 detail-panel contract missing: {token}")

    # v1.4 Stage 10 attachment/media contract across geometry families.
    for token in [
        "ATTACHMENT_MEDIA_FIELD", "classify_attachment", "attachment_media",
        "attachmentSummary", "Image and audio", "video/other media"
    ]:
        if token not in fetch_script:
            error("ATTACHMENT_MEDIA_EXPORT", f"Stage 10 media-export contract missing: {token}")
    for token in [
        "normalizeAttachmentMedia", "attachmentMedia", "inferAttachmentKind"
    ]:
        if token not in entities:
            error("ATTACHMENT_MEDIA_ENTITY", f"Stage 10 Entity media contract missing: {token}")
    for token in [
        "Photos", "Audio", "Other Attachments", "entity-detail-other-item",
        "<source src=", "Open video"
    ]:
        if token not in details + css:
            error("ATTACHMENT_MEDIA_UI", f"Stage 10 media UI contract missing: {token}")
    qa_data = read("scripts/qa_data.py")
    for token in [
        "ATTACHMENT_MEDIA_INVALID", "ATTACHMENT_MEDIA_MISMATCH",
        "mediaKinds", "mediaStorage", "attachmentMediaField"
    ]:
        if token not in qa_data + read("scripts/qa_config.json"):
            error("ATTACHMENT_MEDIA_QA", f"Stage 10 media QA contract missing: {token}")

    # Data fetching/cache behavior.
    if "cache: 'no-store'" not in data_js or "Date.now()" not in data_js:
        error("DATA_CACHE_BUSTING", "Generated JSON/config loads must retain no-store cache busting.")

    # Sidecar must remain website-managed and structurally valid.
    try:
        sidecar = json.loads(read("data/site/poi-meta.json"))
        if sidecar.get("schemaVersion") != 1 or not isinstance(sidecar.get("entities"), dict):
            error("SIDECAR_SCHEMA", "data/site/poi-meta.json does not match the Stage 5 sidecar schema.")
    except Exception as exc:
        error("SIDECAR_JSON", f"Unable to parse data/site/poi-meta.json: {exc}")

    # Version should be internally consistent during development and release.
    version = read("VERSION").strip()
    if not version:
        error("VERSION_EMPTY", "VERSION is empty.")
    elif f"v{version}" not in html:
        warning("VERSION_TITLE_MISMATCH", f"VERSION is {version}, but index.html title does not contain v{version}.")

    return finish(issues)


def finish(issues: list[Issue]) -> int:
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    status = "ERROR" if errors else ("WARNING" if warnings else "PASS")

    print(f"Frontend regression QA: {status}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    for issue in issues:
        print(f"[{issue.severity}] {issue.code}: {issue.message}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("\n## POIS Travel Science — Frontend Regression QA\n\n")
            handle.write(f"**Status:** {status}  \n")
            handle.write(f"**Errors:** {len(errors)} · **Warnings:** {len(warnings)}\n\n")
            if issues:
                handle.write("### Issues\n\n")
                for issue in issues:
                    icon = "❌" if issue.severity == "ERROR" else "⚠️"
                    handle.write(f"- {icon} **{issue.code}**: {issue.message}\n")
            else:
                handle.write("All static standalone/embed regression contracts passed.\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
