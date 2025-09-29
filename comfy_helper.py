import os
import re
import json

# Custom imports
try:
    from .client import Client
    from .workflow import Workflow
    from .utils.files import max_frame_number
except ImportError:
    from client import Client
    from workflow import Workflow
    from utils.files import max_frame_number


class ComfyHelper:
    def __init__(self, server_address: str):
        self.client = Client(server_address)

    def multi_image_single_prompt_IMG2IMG(
        self,
        workflow_path: str,
        source_dir: str,
        output_prefix: str,
        prompt: str = "",
        reference_dir: str = "",
        reference_prefix: str = "",
        override_index: int = -1,
        file_paths: list = [],
    ):
        """
        Use multiple images and a single prompt to generate further images.

        Parameters
        ----------
        workflow_name : str
            Name of the workflow.
        source_dir : str
            Directory to get images from.
        server_address : str
            Address of the server.
        output_prefix : str
            Prefix to use for the file when it is saved.
        file_paths : list, optional
            Optionally provide a list of files to override the automatic search, by default []
        """
        self.client.connect()
        workflow = Workflow(workflow_path)
        base_file = os.listdir(source_dir)
        base_file = sorted(base_file, key=lambda s: int(re.search(r"\d+", s).group()))
        if reference_dir != "" and override_index == -1:
            max_frame = max_frame_number(reference_dir, reference_prefix)
            base_file = base_file[max_frame - 1 :]
            # base_file = self._get_missing_frames(source_dir, reference_dir)

        if override_index != -1:
            base_file = base_file[override_index:]
        try:
            if file_paths != []:
                for i in file_paths:
                    workflow_data = workflow.edit_workflow(
                        pos_prompt=prompt,
                        neg_prompt="",
                        image_path=i,
                        prefix=output_prefix,
                    )
                    print(f"Executing prompt: {prompt}   Image: {i}")
                    print(workflow_data)
                    self.execute_IMG2IMG(workflow_data)
            else:
                for i in base_file:
                    image_path = os.path.join(source_dir, i)
                    workflow_data = workflow.edit_workflow(
                        pos_prompt=prompt,
                        neg_prompt="",
                        image_path=image_path,
                        prefix=output_prefix,
                    )
                    print(f"Executing prompt: {prompt}   Image: {i}")
                    self.execute_IMG2IMG(workflow_data)
        except KeyboardInterrupt:
            pass
        self.client.connection.close()
        print(f"Client Closed")

    def singe_image_multi_prompt_IMG2IMG(
        self,
        workflow_path: str,
        prompts: list,
        image_path: str,
        output_prefix: str,
    ):
        self.client.connect()
        workflow = Workflow(workflow_path)
        try:
            for p in prompts:
                workflow_data = workflow.edit_workflow(p, "", image_path, output_prefix)
                print(f"Executing prompt: {p}")
                self.execute_IMG2IMG(workflow_data)
        except KeyboardInterrupt:
            pass
        self.client.connection.close()

    def multi_image_multi_prompt_IMG2IMG(
        self,
        workflow_path: str,
        images_or_dir: str | list,
        prompts: list,
        output_prefix: str,
    ):
        self.client.connect()
        workflow = Workflow(workflow_path)
        if isinstance(images_or_dir, str):
            images = os.listdir(images_or_dir)
            images_or_dir = [os.path.join(images_or_dir, image) for image in images]
        try:
            for i in images_or_dir:
                for p in prompts:
                    workflow_data = workflow.edit_workflow(
                        pos_prompt=p, neg_prompt="", image_path=i, prefix=output_prefix
                    )
                    print(f"Executing prompt: {p}")
                    self.execute_IMG2IMG(workflow_data)
        except KeyboardInterrupt:
            pass
        self.client.connection.close()

    """
    ===================================================================================
    Workflow execution
    ===================================================================================
    """

    def _execute_workflow(self, workflow_data: dict):
        prompt_id = self.client.queue_prompt(workflow_data)["prompt_id"]
        print(f"PROMPT ID: {prompt_id}")
        while True:
            out = self.client.connection.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message["type"] == "executing":
                    data = message["data"]
                    if data["node"] is None and data["prompt_id"] == prompt_id:
                        break  # Execution complete
            else:
                # Binary data (preview images)
                continue

        # Get history for the executed prompt
        history = self.client.get_history(prompt_id)[prompt_id]
        # Since a ComfyUI workflow may contain multiple SaveImage nodes,
        # and each SaveImage node might save multiple images,
        # we need to iterate through all outputs to collect all generated images
        output_images = {}
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            images_output = []
            if "images" in node_output:
                for image in node_output["images"]:
                    image_data = self.client.get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

    def execute_IMG2IMG(self, workflow_data: dict):
        self._execute_workflow(workflow_data)

    def _get_missing_frames(self, source_dir: str, target_dir: str):
        result = [x for x in os.listdir(source_dir) if x not in os.listdir(target_dir)]
        result = sorted(result, key=lambda x: int(re.search(r"\d+", x).group()))
        return result
