import asyncio
import datetime
import os

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    TextSearchIndexType
)


async def get_text_retelling(user_prompt):
    system_prompt = ('Тебе необходимо кратко пересказать текст. '
                     'Ничего не додумывай, придерживайся только текущего текста')
    messages = [
        {'role': 'system', 'text': system_prompt},
        {'role': 'user', 'text': user_prompt},
    ]

    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    model = sdk.models.completions('yandexgpt-lite')
    model.configure(
        temperature=0.3,
        max_tokens=4000,
    )
    operation = model.run_deferred(messages)

    status = operation.get_status()
    while status.is_running:
        await asyncio.sleep(3)
        status = operation.get_status()

    result = operation.get_result()
    print(result)
    return result.text


async def get_img(user_prompt):
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    model = sdk.models.image_generation('yandex-art')
    model.configure(
        seed=int(round(datetime.datetime.now().timestamp())),
    )

    messages = [
        {"weight": 1, "text": user_prompt},
    ]

    operation = model.run_deferred(messages)

    status = operation.get_status()
    while status.is_running:
        await asyncio.sleep(3)
        status = operation.get_status()

    result = operation.get_result()
    print(result)
    return result.image_bytes


async def get_text_category(user_prompt):
    CATEGORIES = [
        'Научный', 'Научно-популярный', 'Публицистический', 'Художественный', 'Официально-деловой', 'Разговорный'
    ]

    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    model = sdk.models.text_classifiers("yandexgpt").configure(
        task_description="Определи жанр текста",
        labels=CATEGORIES
    )

    result = model.run(user_prompt)

    best_prediction = result.predictions[0]
    for prediction in result.predictions:
        if prediction.confidence > best_prediction.confidence:
            best_prediction = prediction

    print(best_prediction)
    return f'Это {best_prediction.label} текст'


async def create_assistant(list_of_data):
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    operation = sdk.search_indexes.create_deferred(list_of_data, index_type=TextSearchIndexType())

    status = operation.get_status()
    while status.is_running:
        await asyncio.sleep(3)
        status = operation.get_status()

    text_index = operation.get_result()
    text_tool = sdk.tools.search_index(text_index)
    model = sdk.models.completions("yandexgpt", model_version="rc")
    assistant = sdk.assistants.create(model, tools=[text_tool])

    return assistant.id


async def get_ans_by_assist(user_prompt, assistant_id):
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    assistant = sdk.assistants.get(assistant_id)

    text_index_thread = sdk.threads.create()
    text_index_thread.write(user_prompt)
    run = assistant.run(text_index_thread)

    result = run.wait().message
    for part in result.parts:
        print(part)
