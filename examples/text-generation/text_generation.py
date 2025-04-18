import os

from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML

load_dotenv()

def main1():
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    model = sdk.models.completions('yandexgpt-lite')
    model.configure(
        temperature=0.2,
        max_tokens=4000,
    )

    system_prompt = 'Ты ассистент программиста. Распознай, на каком языке написан код и исправь в нем ошибки. Дай краткие комментарии по тому, что ты исправил.'
    user_prompt = open('code.txt', mode='r', encoding='utf-8').read()
    messages = [
        {'role': 'system', 'text': system_prompt},
        {'role': 'user', 'text': user_prompt},
    ]

    operation = model.run_deferred(messages)
    result = operation.wait()
    print(result.text)


main1()
