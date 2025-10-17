print("Проверка импорта...")

try:
    print("Импортируем mmdet...")
    from mmdet.apis import init_detector, inference_detector
    print("mmdet успешно импортирован!")

    print("Импортируем остальные модули...")
    from mmdet.utils import register_all_modules
    from mmengine.config import Config
    print("Остальные модули успешно импортированы!")

    register_all_modules()
    print("Модули зарегистрированы!")

    # Укажи правильные пути к файлам
    config_file = 'faster_rcnn_r50_fpn_1x_coco.py'
    checkpoint_file = 'faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth'

    print("Загружаем модель...")
    model = init_detector(config_file, checkpoint_file, device='cpu')  # или 'cuda'
    print("Модель успешно загружена!")

except Exception as e:
    print(f"Ошибка: {e}")