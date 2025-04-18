import asyncio
import aiohttp
import os
import requests

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    TextSearchIndexType
)
from core.database.config import settings


async def create_assistant():
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    data = [
        sdk.files.upload(f'core/data/method{i}.txt') for i in range(1, 6)
    ]
    operation = sdk.search_indexes.create_deferred(data, index_type=TextSearchIndexType())

    status = operation.get_status()
    while status.is_running:
        await asyncio.sleep(5)
        status = operation.get_status()

    text_index = operation.get_result()
    text_tool = sdk.tools.search_index(text_index)
    model = sdk.models.completions("yandexgpt", model_version="rc")
    assistant = sdk.assistants.create(model, tools=[text_tool])

    return assistant.id


async def get_ans_by_assist(exp, spec, place):
    assistant_id = await create_assistant()
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    assistant = sdk.assistants.get(assistant_id)

    text_index_thread = sdk.threads.create()
    text_index_thread.write(f'Дай советы по тому, как улучшить преподавание уроков. Приведи примеры (удачные и неудачные).'
                            f' Информация о пользователе: опыт: {exp}, специальность: {spec}, место работы: {place}')
    print('отправлено')
    run = assistant.run(text_index_thread)

    res = ''
    result = run.wait().message
    for part in result.parts:
        print(part)
        res += str(part)
    return res


async def create(file_path):
    headers = {"keyId": settings.API_KEY_ID, "keySecret": settings.API_KEY_SECRET}
    files = {}
    create_url = "https://api.speechflow.io/asr/file/v1/create"
    create_url += "?lang=" + 'ru'
    files['file'] = open(file_path, "rb")
    # async with aiohttp.ClientSession() as session:
    #     response = await session.post(create_url, headers=headers, files=files)
    response = requests.post(create_url, headers=headers, files=files)
    if response.status_code == 200:
        create_result = response.json()
        print(create_result)
        if create_result["code"] == 10000:
            task_id = create_result["taskId"]
        else:
            print("create error:")
            print(create_result["msg"])
            task_id = ""
    else:
        print('create request failed: ', response.status_code)
        task_id = ""
    return task_id


async def query(task_id):
    headers = {"keyId": settings.API_KEY_ID, "keySecret": settings.API_KEY_SECRET}
    query_url = "https://api.speechflow.io/asr/file/v1/query?taskId=" + task_id + "&resultType=4"
    print('querying transcription result')
    while True:
        response = requests.get(query_url, headers=headers)
        if response.status_code == 200:
            query_result = response.json()
            if query_result["code"] == 11000:
                print('transcription result')
                return query_result['result']
            elif query_result["code"] == 11001:
                print('waiting')
                await asyncio.sleep(3)
            else:
                print(query_result)
                print("transcription error")
                return query_result['msg']
        else:
            print('query request failed: ', response.status_code)


async def get_stt(file_path):
    task_id = await create(file_path)
    if task_id != "":
        return await query(task_id)
    return 'ошибка'


async def get_text(user_prompt, data, update, questions=False):
    system_prompt = ('Ты - профессиональный спикер. Посмотри данный текст и дай рекомендации по его улучшению. '
                     'Пользователь - эскперт IT индустрии, но хочет начать преподавать. Ему надо дать советы по '
                     f'soft-skills и психологические советы. Информация о пользователе: {data}')
    if questions:
        system_prompt = ('Представь, что ты - студент. Задай трудные для преподавателя вопросы, '
                         'над которыми нужно подумать и которые помогут в тренировке речи преподавателя.')
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
        temperature=0.4,
        max_tokens=4000,
    )
    await update.message.reply_text('отправлено')
    operation = model.run_deferred(messages)

    status = operation.get_status()
    while status.is_running:
        await asyncio.sleep(5)
        status = operation.get_status()

    result = operation.get_result()
    return result.text
