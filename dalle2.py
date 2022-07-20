import base64
import json
import os
import requests
import time 
import urllib
import urllib.request

from PIL import Image
from pillow_utils import *

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
            # print(f"{response=}")
            data = response.json()
            # print(f"{data=}")
            
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
                print("...Task not completed yet")
                time.sleep(self.sleep_seconds)
                continue

    def download(self, generations, n=1, image_dir=os.getcwd(), file_name=None):
        if not generations:
            raise ValueError("generations is empty!")
        
        print(f"Download to directory: {image_dir}")
        
        file_paths = []
        for i, generation in enumerate(generations[:n]):
            image_url = generation["generation"]["image_path"]
            file_name = f"{file_name}_{i}" if file_name else generation['id']
            file_path = f"{image_dir}/{file_name}.jpg"
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

# 1 to the sides (3 calls)
def generate_2048_1024(prompt, _flavor, image_dir):
    # generate the root image
    filepaths = dalle.generate_and_download(prompt, image_dir=image_dir, file_name='root')
    root = Image.open(filepaths[0])
    m, _n = root.size

    # flip left & right
    rolled = roll_horizontally(root.copy(), m//2)
    
    # extend RHS of root image
    transparent_crop(rolled.copy(), 'right').save(f"{image_dir}/right_mask.png")
    generations = dalle.generate_from_masked_image(f"{image_dir}/right_mask.png", prompt)
    filepaths = dalle.download(generations, image_dir=image_dir, file_name='right')
    right = Image.open(filepaths[0])

    # extend LHS of root image
    transparent_crop(rolled.copy(), 'left').save(f"{image_dir}/left_mask.png")
    generations = dalle.generate_from_masked_image(f"{image_dir}/left_mask.png", prompt)
    filepaths = dalle.download(generations, image_dir=image_dir, file_name='left')
    left = Image.open(filepaths[0])
    
    # stitch images together
    return merge_horizontally_sequentially([left, root, right], overlap=m//2)

# 1 up & to the sides (9 calls)
def generate_2048_2048(prompt, flavor, image_dir):
    pass

# 3 in all directions (46 calls)
def generate_8192_8192(prompt, flavor, image_dir):
    pass

# 2 up, 4 to the sides (45 calls)
def generate_10240_6144(prompt, flavor, image_dir):
    pass

