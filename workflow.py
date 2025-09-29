import json, secrets


class Workflow:
    def __init__(self, workflow_path: str):
        self.data = self._load_workflow(workflow_path)
        self.original_state = self.data  # Keep copy of original state

    def _load_workflow(self, workflow_path: str):
        with open(workflow_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    def view_workflow(self, isolate_node=None):

        for k, v in self.data.items():
            if isolate_node == None:
                print(k, v)
            else:
                if k == isolate_node:
                    print(k, v)

    def edit_workflow(
        self,
        pos_prompt: str,
        neg_prompt: str,
        image_path: str,
        prefix: str,
        steps: int = -1,
        seed: int = -1,
    ):
        new_workflow = self.data
        ksampler_key = self._find_ksampler_node_key()
        prompt_key = self._find_prompt_node_key()

        if pos_prompt != "":
            new_workflow = self.write_node_values(
                new_workflow, prompt_key[0], pos_prompt, "prompt"
            )
        if neg_prompt != "":
            new_workflow = self.write_node_values(
                new_workflow, prompt_key[1], pos_prompt, "prompt"
            )
        if image_path != "":
            image_key = self._find_image_node_key()
            new_workflow = self.write_node_values(
                new_workflow, node_key=image_key, value=image_path, value_key="image"
            )

        if prefix != "":
            save_image_key = self._find_save_image_node_key()
            if isinstance(save_image_key, str | int):
                new_workflow = self.write_node_values(
                    new_workflow,
                    node_key=save_image_key,
                    value=prefix,
                    value_key="filename_prefix",
                )
            elif isinstance(save_image_key, list):
                for n in save_image_key:
                    new_workflow = self.write_node_values(
                        new_workflow,
                        node_key=n,
                        value=prefix,
                        value_key="filename_prefix",
                    )

        if steps != -1:
            new_workflow = self.write_node_values(
                new_workflow, node_key=ksampler_key, value=steps, value_key="steps"
            )

        if seed != -1:
            new_workflow = self.write_node_values(
                new_workflow, node_key=ksampler_key, value=seed, value_key="seed"
            )
        elif seed == -1:
            seed = self._create_seed()
            new_workflow = self.write_node_values(
                new_workflow, node_key=ksampler_key, value=seed, value_key="seed"
            )

        return new_workflow

    def write_node_values(
        self, workflow_data: dict, node_key: str, value: str, value_key: str
    ):
        workflow_data[node_key]["inputs"][value_key] = value
        return workflow_data

    def _create_seed(self, bits=32) -> int:
        return secrets.randbits(bits)

    #     if steps != -1:

    """
    ========================================================
    Find Nodes 
    ========================================================
    """

    def _find_node_key(self, node_class: str):
        nodes = []
        for k1, v1 in self.data.items():
            class_type = v1["class_type"]
            if isinstance(node_class, str):
                if class_type == node_class:
                    nodes.append(k1)
            elif isinstance(node_class, list):
                if class_type in node_class:
                    nodes.append(k1)
        if len(nodes) > 1:
            return nodes
        elif len(nodes) == 1:
            return nodes[0]
        else:
            return nodes

    def _find_image_node_key(self) -> str | list:
        key = self._find_node_key("LoadImage")
        return key

    def _find_save_image_node_key(self) -> str | list:
        node_classes = ["SaveImage", "VHS_VideoCombine"]
        key = self._find_node_key(node_classes)
        return key

    def _find_prompt_node_key(self):
        node_classes = ["CLIPTextEncode", "TextEncodeQwenImageEdit"]
        key = self._find_node_key(node_class=node_classes)
        return key

    def _find_ksampler_node_key(self):
        node_classes = ["KSampler", "KSamplerAdvanced"]
        key = self._find_node_key(node_class=node_classes)
        return key
