import os
import urllib.request
from pathlib import Path

models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

urls = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
}

for filename, url in urls.items():
    filepath = models_dir / filename
    if not filepath.exists():
        print(f"Pobieranie najnowszego modelu SI {filename} (to może chwilę potrwać)...")
        try:
            urllib.request.urlretrieve(url, str(filepath))
            print(f"✓ {filename} pobrany pomyślnie.")
        except Exception as e:
            print(f"Błąd podczas pobierania {filename}: {e}")
