# Point of Interest (POI) Map - v1.2.0

An interactive Leaflet.js web mapping application for displaying Points of Interest (POIs) collected with Esri Field Maps. The website is static at runtime: data and attachments are periodically synchronized from the ArcGIS Feature Service into local files in the repository.

---

## What's New in v1.2.0

- **Timezone Layer Stability Fix:** Vector timezone boundaries are loaded from a CDN with an Esri World Time Zones fallback.
- **Light Basemap Replacement:** Uses **Esri Light Gray Canvas**, avoiding API-key watermarks.
- **Interactive Legend & Topic Filtering:** Topic categories can be toggled directly from the legend.
- **Real-Time Coordinate Tracker:** Displays cursor latitude and longitude.
- **Built-In POI Search:** Searches POIs by name and opens the selected feature.
- **Embed Mode (`embed=true`):** Hides the top header for iframe embedding.

---

## Key Features

- Five basemaps: OpenStreetMap, Esri World Imagery, Esri Topographic, Esri Light Gray Canvas, and National Geographic / Esri.
- Day/night solar terminator overlay.
- World timezone overlay with fallback loading.
- Custom SVG marker shapes and colors configured in `config.json`.
- Interactive topic legend and filtering.
- POI-name search.
- Rich popups with feature attributes, coordinates, and image attachments.
- Local, static runtime data for fast deployment and simple hosting.

---

## Data Workflow

POIs are collected in **Esri Field Maps** and stored in the ArcGIS Feature Service. A scheduled **GitHub Actions** workflow runs once per week and uses `scripts/fetch_data.py` to refresh the repository data.

The update process generates or refreshes:

- `data/pois.geojson` — primary dataset used by the web map.
- `data/pois.csv` — tabular export.
- `data/pois.pdf` — PDF export when PDF dependencies are available.
- `data/attachments/` — locally stored image attachments.

Because the weekly workflow updates data independently of application releases, data-refresh commits should be distinguished from code/configuration changes when reviewing history, debugging, or performing QA.

---

## Project Structure

```text
.
├── .git/                 # Local Git metadata (not part of distributed source files)
├── .github/              # GitHub Actions workflows and repository automation
├── data/
│   ├── attachments/      # Locally stored POI image attachments
│   ├── pois.geojson      # Primary dataset loaded by the web map
│   ├── pois.csv          # CSV export
│   └── pois.pdf          # PDF export
├── scripts/
│   └── fetch_data.py     # ArcGIS data/attachment synchronization and export script
├── .gitattributes
├── config.json           # Initial map settings and topic symbology
├── index.html            # Leaflet application, styling, and client-side logic
├── README.md             # Project documentation
└── VERSION               # Current application version
```

---

## Local Preview

Run a local HTTP server from the repository root (do not open `index.html` directly with `file://`):

```cmd
py -m http.server 8000
```

Then open:

```text
http://localhost:8000/
```

---

## Runtime Architecture

At runtime, `index.html` loads `config.json` and `data/pois.geojson` from the repository. The browser does **not** query the ArcGIS Feature Service directly. ArcGIS synchronization is handled separately by `scripts/fetch_data.py` and the scheduled GitHub Actions workflow.

---

## Version

Current release: **1.2.0**
