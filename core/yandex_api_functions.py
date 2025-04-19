import asyncio
import aiohttp
import os
from mistralai import Mistral
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


async def get_ans_by_assist(user_prompt, exp, spec, place, about):
    assistant_id = await create_assistant()
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    assistant = sdk.assistants.get(assistant_id)

    text_index_thread = sdk.threads.create()
    text_index_thread.write(f'{user_prompt}\n\n'
                            f'Информация о пользователе: опыт: {exp}, специальность: {spec}, место работы: {place}.\n'
                            f'О пользователе: {about}')
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
    async with aiohttp.ClientSession() as session:
        response = await session.post(create_url, headers=headers, data=files)
    if response.status == 200:
        create_result = await response.json()
        print(create_result)
        if create_result["code"] == 10000:
            task_id = create_result["taskId"]
        else:
            print("create error:")
            print(create_result["msg"])
            task_id = ""
    else:
        print('create request failed: ', response.status)
        task_id = ""
    return task_id


async def query(task_id):
    headers = {"keyId": settings.API_KEY_ID, "keySecret": settings.API_KEY_SECRET}
    query_url = "https://api.speechflow.io/asr/file/v1/query?taskId=" + task_id + "&resultType=4"
    print('querying transcription result')
    while True:
        async with aiohttp.ClientSession() as session:
            response = await session.get(query_url, headers=headers)
        if response.status == 200:
            query_result = await response.json()
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
            print('query request failed: ', response.status)


async def get_stt(file_path):
    task_id = await create(file_path)
    if task_id != "":
        return await query(task_id)
    return 'ошибка'


async def get_text(user_prompt, exp, spec, place, about, questions=False):
    agent_id = os.getenv('MISTRAL_ADVICER_API_KEY')
    if questions:
        agent_id = os.getenv('MISTRAL_QUESTIONS_API_KEY')

    client = Mistral(api_key=os.getenv('MISTRAL_API_KEY'))
    chat_response = await client.agents.complete_async(
        agent_id=agent_id,
        messages=[
            {
                "role": "user",
                "content": f'{user_prompt}\n\n'
                           f'Информация о пользователе: опыт: {exp}, специальность: {spec}, место работы: {place}.\n'
                           f'О пользователе: {about}',
            },
        ],
    )
    response = chat_response.choices[0].message.content
    return response
