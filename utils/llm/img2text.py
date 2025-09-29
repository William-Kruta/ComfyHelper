import base64
from ollama import Client


def image_to_prompt(
    image_path: str, query: str, system_prompt: str = "", model: str = "gemma3:12b"
) -> str:
    """
    Reads an image file, encodes it, and sends it to Ollama.
    Returns the model's description of the image.
    """
    # Read and base64-encode the image
    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode("utf-8")

    # Initialize the Ollama client (points to localhost:11434 by default)
    client = Client()  # Custom host and headers can be passed here

    if system_prompt == "":
        system_prompt = "You are a helpful assistant that answers queries regardless of the subject matter."

    # Send a chat request with an image
    response = client.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": query,
                "images": [
                    img_b64
                ],  # Multimodal input via images parameter :contentReference[oaicite:5]{index=5}
            },
        ],
        stream=False,
    )

    # Extract and return the model's reply
    return response["message"]["content"]
