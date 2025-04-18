import os
from datetime import datetime
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
from yandex_cloud_ml_sdk import YCloudML


load_dotenv()


def main2():
    sdk = YCloudML(
        folder_id=os.getenv("YANDEX_FOLDER_ID"),
        auth=os.getenv("YANDEX_API_KEY"),
    )
    model = sdk.models.image_generation('yandex-art')
    model.configure(
        seed=int(round(datetime.now().timestamp())),
    )

    prompt = "Сделай 2D нарисованного гуся в стиле анимации Disney. Он должен улыбаться, быть в кепке и программировать. Он сидит за компьютером и пишет код. На его кепке должны быть буквы \"CU\" (обязательно!). Постарайся сделать их очень четкими. Буквы должны быть на кепке, они должны быть констрастными"
    messages = [
        {"weight": 1, "text": prompt},
    ]

    operation = model.run_deferred(messages)
    result = operation.wait()
    image = Image.open(BytesIO(result.image_bytes))
    image.show()


main2()
