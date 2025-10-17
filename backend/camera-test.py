from fastapi import FastAPI, File, UploadFile
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator  # заменили googletrans

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Загружаем модель
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

@app.post("/api/describe")
async def describe_image(file: UploadFile = File(...)):
    print("Получен файл:", file.filename)
    print("Тип файла:", file.content_type)

    img = Image.open(file.file)
    inputs = processor(img, return_tensors="pt")
    out = model.generate(**inputs)
    description_en = processor.decode(out[0], skip_special_tokens=True)

    print("Описание на английском:", description_en)

    # Переводим на русский
    try:
        description_ru = GoogleTranslator(source='en', target='ru').translate(description_en)
    except Exception as e:
        print("Ошибка перевода:", e)
        description_ru = description_en  # возвращаем английский, если перевод не удался

    print("Описание на русском:", description_ru)

    return {"description": description_ru}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7510)