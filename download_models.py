import os
import urllib.request
from pathlib import Path

models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

urls = {
    "gender_deploy.prototxt": "https://raw.githubusercontent.com/smahesh29/Gender-and-Age-Detection/master/gender_deploy.prototxt",
    "gender_net.caffemodel": "https://raw.githubusercontent.com/smahesh29/Gender-and-Age-Detection/master/gender_net.caffemodel"
}

for filename, url in urls.items():
    filepath = models_dir / filename
    if not filepath.exists():
        print(f"Pobieranie {filename}...")
        try:
            urllib.request.urlretrieve(url, str(filepath))
            print(f"✓ {filename} pobrany pomyślnie.")
        except Exception as e:
            print(f"Błąd podczas pobierania {filename}: {e}")
