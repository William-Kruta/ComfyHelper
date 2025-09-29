import base64
from ollama import Client


def get_response(query: str, system_prompt: str = "", model: str = "gemma3:12b") -> str:
    """
    Reads an image file, encodes it, and sends it to Ollama.
    Returns the model's description of the image.
    """
    # Read and base64-encode the image

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
            },
        ],
        stream=False,
    )
    return response["message"]["content"]


def write_list_to_file(data, filename):
    """Writes a list of strings to a text file, each string on a new line."""
    try:
        with open(filename, "w") as f:
            for item in data:
                f.write(item + "\n")
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False


def read_file_to_list(filename):
    """Reads a text file into a list of strings, where each line is an item."""
    try:
        with open(filename, "r") as f:
            data = [
                line.strip() for line in f
            ]  # Read lines and remove trailing newline characters
        return data
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return []
    except Exception as e:
        print(f"Error reading from file: {e}")
        return []


def create_multiple_prompts(
    seed_prompt: str,
    model: str,
    output_path: str,
    system_prompt: str = "",
    intervals: int = 20,
):
    responses = []
    full_prompt = f"Create a prompt based on this premise: {seed_prompt}. Respond with nothing but the prompt. Have a focus on the pose of the subjects body. Don't be over wordy. Do not mention colors of clothing."
    index = 0
    try:
        while index < intervals:
            resp = get_response(full_prompt, system_prompt=system_prompt, model=model)
            print(f"Response: {resp}   Index: {index}")
            responses.append(resp)
            index += 1
    except KeyboardInterrupt:
        pass
    write_list_to_file(responses, output_path)


if __name__ == "__main__":
    model = "mannix/llama3.1-8b-abliterated:q4_0"
    create_multiple_prompts(
        "A woman wearing a bikini in a room", model, "prompts.txt", intervals=50
    )
