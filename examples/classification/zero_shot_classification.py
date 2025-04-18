import os

from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML

message = open('text.txt', 'r', encoding='utf-8').read()

load_dotenv()
sdk = YCloudML(
    folder_id=os.getenv("YANDEX_FOLDER_ID"),
    auth=os.getenv("YANDEX_API_KEY"),
)

model = sdk.models.text_classifiers("yandexgpt").configure(
    task_description="Определи эмоциональный окрас текста",
    labels=["Человек в депрессии", "Человек в стрессе", "Человек в радости", "Человек в нейтральном состоянии", "Человек в восторге", "Человек в печали", "Человек в гневе", "Человек в страхе", "Человек в скуке"],
)

result = model.run(message)

best_prediction = result.predictions[0]
for prediction in result.predictions:
    if prediction.confidence > best_prediction.confidence:
        best_prediction = prediction

print(best_prediction.label)
