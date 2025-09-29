import uuid
import json

# Web related
import websocket
import urllib.request


class Client:
    def __init__(self, server_address: str, client_id: str = None, log: bool = True):
        self.server_address = server_address
        if client_id == None:
            self.client_id = str(uuid.uuid4())
        else:
            self.client_id = str(client_id)
        self.log = log
        self.connection = None

    def connect(self):
        if self.connection == None:
            self.connection = websocket.WebSocket()
            self.connection.connect(
                f"ws://{self.server_address}/ws?clientId={self.client_id}"
            )
            if self.log:
                print(f"Connected to client...")

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        if self.log:
            print(f"Prompt queued")
        return json.loads(urllib.request.urlopen(req).read())

    def get_history(self, prompt_id):
        with urllib.request.urlopen(
            f"http://{self.server_address}/history/{prompt_id}"
        ) as response:
            return json.loads(response.read())

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            f"http://{self.server_address}/view?{url_values}"
        ) as response:
            return response.read()

    def monitor(self, prompt_id: str):
        while True:
            out = self.connection.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message["type"] == "executing":
                    data = message["data"]
                    if data["node"] is None and data["prompt_id"] == prompt_id:
                        break  # Execution complete
            else:
                # Binary data (preview images)
                continue


if __name__ == "__main__":
    print(websocket.__version__)
    print(urllib.__version__)
