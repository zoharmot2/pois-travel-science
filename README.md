# \# POI Map \& Data Processing Pipeline

# 

# An automated system for fetching, processing, and displaying Points of Interest (POI) from ArcGIS Feature Servers. The pipeline exports structured data into GeoJSON, CSV, and PDF formats, and visualizes the points on an interactive Leaflet.js map.

# 

# \## 🚀 Key Features (Version 1.0.0)

# 

# \* \*\*ArcGIS Data Fetching:\*\* Complete feature extraction with pagination support to handle server record limits.

# \* \*\*Image \& Attachment Processing:\*\* Automatic image downloading, optimization, compression, and EXIF orientation fix (`exif\_transpose`).

# \* \*\*Multi-Format Export:\*\*

# &#x20; \* `data/pois.geojson` – For dynamic web map visualization.

# &#x20; \* `data/pois.csv` – Structured tabular dataset.

# &#x20; \* `data/pois.pdf` – Detailed PDF report with attached images and Hebrew font support (`NotoSansHebrew`).

# \* \*\*Chronological Sorting:\*\* Automatic ordering of features from oldest to newest based on `CreationDate`.

# \* \*\*Interactive Web Map (`index.html`):\*\*

# &#x20; \* Custom symbology using reddish-brown circle markers (`#8B261D`) with white borders.

# &#x20; \* Mouseover hover effects.

# &#x20; \* Clean Left-to-Right (LTR) popups displaying attributes and attached media.

# &#x20; \* Automatic view fitting (`fitBounds`) to display all fetched features.

# 

# \---

# 

# \## 📁 Project Structure

# 

# ```text

# .

# ├── index.html               # Interactive Leaflet map interface

# ├── VERSION                  # Current version tracking file (1.0.0)

# ├── README.md                # Project documentation

# ├── scripts/

# │   └── fetch\_data.py        # Core Python data pipeline script

# └── data/

# &#x20;   ├── pois.geojson         # Processed GeoJSON data

# &#x20;   ├── pois.csv             # Exported CSV file

# &#x20;   ├── pois.pdf             # Formatted PDF report

# &#x20;   └── attachments/         # Downloaded \& optimized media files

