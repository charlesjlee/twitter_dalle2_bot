import base64
import json
import os
import requests
import time 
import urllib
import urllib.request

from PIL import Image
from pillow_utils import roll_horizontally, roll_vertically, transparent_crop, merge_horizontally_sequentially

# grabbed July 17, 2022
# https://github.com/ezzcodeezzlife/dalle2-in-python
# 1. Go to https://labs.openai.com/
# 2. Open Network Tab in Developer Tools
# 3. Type a prompt and press "Generate"
# 4. Look for fetch to https://labs.openai.com/api/labs/tasks
# 5. In the request header look for authorization then get the Bearer Token

class Dalle2():
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        self.batch_size = 4
        self.inpainting_batch_size = 3
        self.sleep_seconds = 5

    def generate(self, prompt):
        body = {
            "task_type": "text2im",
            "prompt": {
                "caption": prompt,
                "batch_size": self.batch_size,
            }
        }
    
        return self.get_task_response(body)

    def get_task_response(self, body):
        url = "https://labs.openai.com/api/labs/tasks"
        headers = {
            'Authorization': "Bearer " + self.bearer_token,
            'Content-Type': "application/json"
        }
    
        response = requests.post(url, headers=headers, data=json.dumps(body))
        if response.status_code != 200:
            print(response.text)
            return None
        data = response.json()
        print(f"✔️ Task created with ID:{data['id']}")
        print("⌛ Waiting for task to finish...")
    
        while True:
            url = f"https://labs.openai.com/api/labs/tasks/{data['id']}"
            response = requests.get(url, headers=headers)
            data = response.json()

            if not response.ok:
                print(f"Request failed with status: {response.status_code}, data: {response.json()}")
                return None
            elif data["status"] == "failed":
                print(f"Task failed: {data['status_information']}")
                return None
            elif data["status"] == "succeeded":
                print("🙌 Task completed!")
                generations = data["generations"]["data"]
                return generations
            else:
                print("...task not completed yet")
                time.sleep(self.sleep_seconds)
                continue

    def download(self, generations, n=1, image_dir=os.getcwd(), file_name=None):
        if not generations:
            raise ValueError("generations is empty!")

        file_paths = []
        for i, generation in enumerate(generations[:n]):
            image_url = generation["generation"]["image_path"]
            
            if file_name:
                file_name = file_name if n == 1 else f"{file_name}_{i}"
            else:
                file_name = generation['id']

            file_path = f"{image_dir}/{file_name}.png"
            file_paths.append(file_path)
            urllib.request.urlretrieve(image_url, file_path)
            print(f"✔️ Downloaded: {file_path}")
        
        return file_paths

    def generate_and_download(self, prompt, n=1, image_dir=os.getcwd(), file_name=None):
        generations = self.generate(prompt)
        if not generations:
            return None

        return self.download(generations, n, image_dir, file_name)
    
    # todo: outpainting
    def generate_from_masked_image(self, image_path, prompt):
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read())

        body = {
            "task_type": "inpainting",
            "prompt": {
                "caption": prompt,
                "batch_size": self.inpainting_batch_size,
                "image": image_base64.decode(),
                "masked_image": image_base64.decode(), # identical since already masked
            }
        }

        return self.get_task_response(body)

    # note: single mask file names so can't be parallelized
    def extend_image_once(self, root, directions, prompt, flavor, image_dir):
        m, n = root.size
        rolled_horizontally = roll_horizontally(root.copy(), m//2)
        rolled_vertically = roll_vertically(root.copy(), n//2)
    
        for direction in directions:
            file_path = f"{image_dir}/{direction}_mask.png"
            rolled = rolled_horizontally if direction in ('left', 'right') else rolled_vertically
            transparent_crop(rolled.copy(), direction).save(file_path)
            generations = self.generate_from_masked_image(file_path, prompt)
            self.download(generations, image_dir=image_dir, file_name=direction)
    
    # 1 to the sides (3 calls)
    def generate_2048_1024(self, prompt, _flavor, image_dir=os.getcwd()):
        self.generate_and_download(prompt, image_dir=image_dir, file_name='root')
        root = Image.open(f"{image_dir}/root.png")
        m, _n = root.size

        self.extend_image_once(root, ['left', 'right'], prompt, _flavor, image_dir)
        return merge_horizontally_sequentially(
            [
                f"{image_dir}/left.png",
                f"{image_dir}/root.png",
                f"{image_dir}/right.png",
            ],
            overlap=m//2,
        )

    # todo: ready to implement next ... but won't because API calls too expensive
    # 1 up & to the sides (9 calls)
    def generate_2048_2048(self, prompt, flavor, image_dir):
        pass    
    
    # 3 in all directions (46 calls)
    def generate_8192_8192(self, prompt, flavor, image_dir):
        pass
    
    # 2 up, 4 to the sides (45 calls)
    def generate_10240_6144(self, prompt, flavor, image_dir):
        pass

# test class and functions
# note: this will make many API calls; it's better to run one line at a time!
if __name__ == "__main__":
    SESSION_BEARER_TOKEN = 'You can find your API key at https://beta.openai.com'
    PROMPT = "portal to another dimension, digital art"
    dalle = Dalle2(SESSION_BEARER_TOKEN)
    
    generations = dalle.generate(PROMPT)
    print(f"{generations=}")

    generations = dalle.generate_from_masked_image(
        "test/test_working_transparent_crop.png",
        PROMPT,
    )
    print(f"{generations=}")
    dalle.download(generations)

    # stitched image generation
    image = dalle.generate_2048_1024(PROMPT, '', 'test')
    image.save('test/final.png')
    image.show()
