# Point of Interest (POI) Map - v1.2.0

An interactive Leaflet.js-based web mapping application designed to display dynamic Points of Interest (POIs), rich feature popups, utility overlays, and customizable category filtering, with built-in support for iframe embedding.

---

## 🚀 What's New in v1.2.0 (Changelog)

- **Timezone Layer Stability Fix:** Migrated vector boundary loading to a high-speed CDN with an automatic fallback mechanism to the Esri World Time Zones tile service, ensuring 100% layer uptime without CORS errors.
- **Light Basemap Replacement (No API Key Required):** Replaced CartoDB tiles with **Esri Light Gray Canvas** to eliminate "API Key Required" watermarks while keeping a clean, modern basemap.
- **Interactive Legend & Topic Filtering:** Users can toggle category visibility directly by clicking topic items inside the dynamic legend panel.
- **Real-Time Coordinate Tracker:** Displays precise cursor coordinates (`Lat` / `Lon`) on hover.
- **Built-In POI Search:** Search for features by name with automatic map pan/zoom and popup trigger.
- **Embed Mode (`embed=true`):** Hides the top navigation header via URL query parameters for seamless `iframe` integration.

---

## 🛠️ Key Features

1. **5 Diverse Basemaps:**
   - OpenStreetMap (Default)
   - Aerial Imagery (Esri World Imagery)
   - Topographic Map (Esri Topo)
   - Light Map (Esri Light Gray Canvas)
   - Historic Map (National Geographic / Esri)

2. **Utility Overlay Layers:**
   - **Day/Night Overlay:** Real-time solar terminator layer (`Leaflet.Terminator`).
   - **World Time Zones:** Timezone boundaries with UTC offsets.

3. **Custom Symbology & Popups:**
   - Vector SVG icons with custom shapes (`circle`, `square`, `triangle`, `diamond`) and colors configured dynamically via `config.json`.
   - Rich popup windows displaying feature properties, coordinates, and linked image attachments.

---

## 📁 Project Structure

```text
.
├── index.html          # Core application logic, styling, and Leaflet setup
├── config.json          # Map settings, initial bounds, and topic symbology
├── data/
│   └── pois.geojson    # Primary GeoJSON feature dataset
└── README.md           # Project documentation