import json
import os
import urllib.request

ARCGIS_REST_URL = "https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&outSR=4326&returnGeometry=true"

def fetch_and_save_geojson():
    os.makedirs("data", exist_ok=True)
    print("שולף נתונים מ-ArcGIS REST API...")
    
    req = urllib.request.Request(
        ARCGIS_REST_URL, 
        headers={"User-Agent": "Mozilla/5.0"}
    )
    
    with urllib.request.urlopen(req) as response:
        geojson_data = json.loads(response.read().decode("utf-8"))

    output_path = "data/pois.geojson"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    print(f"הנתונים שנשלפו נשמרו בהצלחה ב-{output_path}")

if __name__ == "__main__":
    fetch_and_save_geojson()