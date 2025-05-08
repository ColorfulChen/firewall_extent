import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
load_dotenv()

def image_detection(image_path):
    try:
        endpoint = os.environ["VISION_ENDPOINT_AZURE"]
        key = os.environ["VISION_KEY_AZURE"]
    except KeyError:
        print("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'")
        print("Set them before running this sample.")
        exit()

    # Create an Image Analysis client
    client = ImageAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    # [START read]
    # Load image to analyze into a 'bytes' object
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Extract text (OCR) from an image stream. This will be a synchronously (blocking) call.
    result = client.analyze(
        image_data=image_data,
        visual_features=[VisualFeatures.READ]
    )

    # Print text (OCR) analysis results to the console
    results = ""
    # print("Image analysis results:")
    # print(" Read:")
    if result.read is not None:
        for line in result.read.blocks[0].lines:
            # print(f"   Line: '{line.text}', Bounding box {line.bounding_polygon}")
            for word in line.words:
                # print(f"     Word: '{word.text}', Bounding polygon {word.bounding_polygon}, Confidence {word.confidence:.4f}")
                results = results + word.text
    
    results = results.replace("\n", " ")
    return results
    # [END read]
    # print(f" Image height: {result.metadata.height}")
    # print(f" Image width: {result.metadata.width}")
    # print(f" Model version: {result.model_version}")