import os
import urllib.request
from pathlib import Path

models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

urls = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "gender_deploy.prototxt": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/gender_deploy.prototxt",
    "gender_net.caffemodel": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/gender_net.caffemodel",
    "age_deploy.prototxt": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/age_deploy.prototxt",
    "age_net.caffemodel": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/age_net.caffemodel",
    "emotion_ferplus.onnx": "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
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
