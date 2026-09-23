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
        "data/site/poi-meta.json", "scripts/qa_data.py", "scripts/qa_config.json"
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
    for token in ["Search POI by name...", "Day/Night", "Time Zones", "coordsDisplay", "L.terminator"]:
        if token not in map_js:
            error("MAP_CONTROL_REGRESSION", f"Expected map utility/control missing: {token}")
    if "SEARCH_DELAY_MS = 180" not in map_js or "findBestMatchingLayer" not in map_js:
        error("SEARCH_REGRESSION", "Optimized debounced single-result search contract is missing.")

    # Separate extensible Topic/Type filters.
    for token in ["Research Topics", "POI Types", "createTopicFilterItems", "createTypeFilterItems", "filterEntitiesByDimensions"]:
        if token not in filters + app:
            error("FILTER_REGRESSION", f"Topic/Type filtering contract missing: {token}")
    if "extraValues" not in filters or "observedCounts" not in filters:
        error("TOPIC_EXTENSIBILITY", "Topic filters must include observed values not yet configured.")
    if "getDimensionValues(entities, 'type')" not in filters:
        error("TYPE_EXTENSIBILITY", "POI Type filters must be derived from live Entity data.")
    if "unconfiguredTopics" not in app or "default style" not in app.lower():
        error("TOPIC_FALLBACK", "Unconfigured Topics must remain visible with a default style and warning.")

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
