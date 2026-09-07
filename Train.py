"""
Модуль для обучения модели распознавания лиц.
Этот скрипт обрабатывает датасет с фотографиями людей, извлекает эмбеддинги лиц
с помощью предобученной модели FaceNet и сохраняет эталонные векторы для каждого человека.

Структура датасета:
dataset/
    person1/
        image1.jpg
        image2.jpg
        ...
    person2/
        image1.jpg
        image2.jpg
        ...
    ...

Выходные файлы:
models/
    face_recognition_model.pth  # Модель с эмбеддингами (PyTorch checkpoint)
    face_embeddings.pkl         # Эмбеддинги в формате pickle для отладки

"""

import os
import pickle

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from tqdm import tqdm

DATASET_DIR = './dataset'
MODEL_DIR = './models'
OUTPUT_MODEL = os.path.join(MODEL_DIR, 'face_recognition_model.pth')
OUTPUT_EMBEDDINGS = os.path.join(MODEL_DIR, 'face_embeddings.pkl')
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

os.makedirs(MODEL_DIR, exist_ok=True)

def load_model():
    """Загружает MTCNN и предобученную модель InceptionResnetV1"""
    print(f"Используется устройство: {DEVICE}")
    
    mtcnn = MTCNN(
        image_size=160,
        margin=0,
        min_face_size=20,
        thresholds=[0.6, 0.7, 0.7],
        factor=0.709,
        post_process=True,
        device=DEVICE
    )
    
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)
    
    return mtcnn, resnet

def process_image(image_path, mtcnn, resnet):
    """Обрабатывает одно изображение: находит лицо и возвращает эмбеддинг"""
    try:
        img = Image.open(image_path).convert('RGB')
        
        face_tensor = mtcnn(img)
        
        if face_tensor is None:
            return None
        
        face_tensor = face_tensor.unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            embedding = resnet(face_tensor).squeeze().cpu().numpy()
        
        return embedding
    except Exception as e:
        print(f"Ошибка при обработке {image_path}: {e}")
        return None

def main():
    print("Загрузка моделей...")
    mtcnn, resnet = load_model()
    
    persons = [d for d in os.listdir(DATASET_DIR) 
               if os.path.isdir(os.path.join(DATASET_DIR, d))]
    
    if not persons:
        print("В папке dataset не найдено подпапок с данными.")
        return
    
    print(f"Найдено {len(persons)} человек(а).")
    
    embeddings_dict = {}
    class_names = []
    
    total_images = 0
    successful_faces = 0
    
    for person_name in tqdm(persons, desc="Обработка людей"):
        person_dir = os.path.join(DATASET_DIR, person_name)
        
        image_files = [f for f in os.listdir(person_dir) 
                       if f.lower().endswith(IMAGE_EXTENSIONS)]
        
        if not image_files:
            print(f"В папке {person_name} нет изображений, пропускаем.")
            continue
        
        embeddings_list = []
        
        for img_file in image_files:
            img_path = os.path.join(person_dir, img_file)
            emb = process_image(img_path, mtcnn, resnet)
            if emb is not None:
                embeddings_list.append(emb)
                successful_faces += 1
            total_images += 1
        
        if embeddings_list:
            avg_embedding = np.mean(embeddings_list, axis=0)
            embeddings_dict[person_name] = avg_embedding
            class_names.append(person_name)
        else:
            print(f"Не удалось извлечь лица для {person_name}, пропускаем.")
    
    print(f"\nОбработано изображений: {total_images}, успешно извлечено лиц: {successful_faces}")
    print(f"Сохранено эмбеддингов для {len(embeddings_dict)} человек.")
    
    checkpoint = {
        'class_names': class_names,
        'embeddings': embeddings_dict
    }
    torch.save(checkpoint, OUTPUT_MODEL)
    print(f"Модель сохранена в {OUTPUT_MODEL}")
    
    with open(OUTPUT_EMBEDDINGS, 'wb') as f:
        pickle.dump(embeddings_dict, f)
    print(f"Эмбеддинги сохранены в {OUTPUT_EMBEDDINGS}")

if __name__ == '__main__':
    main()