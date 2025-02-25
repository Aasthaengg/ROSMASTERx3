import numpy as np
import cv2
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer

class Moondream:
    def __init__(self):
        print("\033[96mLoading Moondream Model..\033[0m", end='', flush=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            "vikhyatk/moondream2",
            revision="2025-01-09",
            trust_remote_code=True,
            # Uncomment to run on GPU.
            device_map={"": "cuda"}
        )

    def caption(
            self, 
            image: Image.Image, 
            length: str = "short"
        ):
        return self.model.caption(image, length=length)["caption"]
    
    def query(
            self, 
            image: Image.Image, 
            question: str
        ):
        return self.model.query(image, question)["answer"]
    
    def detect(
            self, 
            image: Image.Image, 
            object_type: str
        ):
        return self.model.detect(image, object_type)["objects"]
    
    def point(
            self, 
            image: Image.Image, 
            object_type: str
        ):
        return self.model.point(image, object_type)["points"]
    
    
    def process_frame(self, frame: np.ndarray, commands: dict):
        """
        Dynamically processes frame based on commands.

        :param frame: The captured video frame.
        :param commands: Dictionary of Moondream functions to execute.
        """
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        results = []

        for cmd, param in commands.items():
            if cmd == "caption":
                res = self.caption(image, length="normal")
                results.append(("Caption", res))
                print("\033[94mCaption:\033[0m", res)

            elif cmd == "query":
                res = self.query(image, param)  # Query expects a question
                results.append(("Query Answer", res))
                print("\033[94mQuery Answer:\033[0m", res)

            elif cmd == "detect":
                res = self.detect(image, param)  # Detect expects an object type
                results.append(("Detected Objects", res))
                print("\033[94mDetected Objects:\033[0m", res)

            elif cmd == "point":
                res = self.point(image, param)  # Point expects an object type
                results.append(("Pointed Objects", res))
                print("\033[94mPointed Objects:\033[0m", res)

        return results