import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import time
import os


# 使用类来管理模型状态，避免全局变量问题
class BLIP2ImageCaptioner:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """Initialize the BLIP2 model and processor"""
        print("Initializing BLIP2-OPT-2.7B model (CPU version)...")
        start_time = time.time()

        try:
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                "Salesforce/blip2-opt-2.7b",
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
            self.processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
            print(f"Model initialized in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")


def image_detection(image_path: str) -> str:
    """
    Analyze an image and return a descriptive caption.

    Args:
        image_path: Path to the image file

    Returns:
        str: The generated caption for the image
    """
    try:
        # Initialize model (singleton pattern ensures it only loads once)
        captioner = BLIP2ImageCaptioner()

        # Open and validate image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = Image.open(image_path).convert("RGB")

        # Optimize image size
        if max(image.size) > 512:
            image.thumbnail((512, 512))

        # Generate caption - 这里确保使用实例的processor和model
        inputs = captioner.processor(image, return_tensors="pt").to("cpu")
        generated_ids = captioner.model.generate(**inputs, max_new_tokens=30)
        caption = captioner.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

        return caption if caption else "No caption generated"

    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return f"Error: {str(e)}"