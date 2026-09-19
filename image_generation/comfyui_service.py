import json
import time
import uuid
from pathlib import Path

import requests


class ComfyUIService:

    def __init__(
        self,
        host: str = "http://127.0.0.1:8188"
    ):
        self.host = host.rstrip("/")

        self.workflow_path = (
            Path(__file__).parent
            / "workflows"
            / "flux2_klein_4b_api.json"
        )

    def _load_workflow(self) -> dict:
        with open(
            self.workflow_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def generate_image(
        self,
        prompt: str,
        timeout: int = 300
    ) -> str:

        workflow = self._load_workflow()

        # Node 76 = Prompt
        workflow["76"]["inputs"]["value"] = prompt

        client_id = str(uuid.uuid4())

        response = requests.post(
            f"{self.host}/prompt",
            json={
                "prompt": workflow,
                "client_id": client_id
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        prompt_id = result["prompt_id"]

        start_time = time.time()

        while time.time() - start_time < timeout:

            history_response = requests.get(
                f"{self.host}/history/{prompt_id}",
                timeout=30
            )

            history_response.raise_for_status()

            history = history_response.json()

            if prompt_id in history:

                outputs = history[prompt_id].get(
                    "outputs",
                    {}
                )

                for node_output in outputs.values():

                    images = node_output.get(
                        "images",
                        []
                    )

                    if images:

                        image = images[0]

                        filename = image["filename"]
                        subfolder = image.get(
                            "subfolder",
                            ""
                        )
                        image_type = image.get(
                            "type",
                            "output"
                        )

                        image_response = requests.get(
                            f"{self.host}/view",
                            params={
                                "filename": filename,
                                "subfolder": subfolder,
                                "type": image_type
                            },
                            timeout=60
                        )

                        image_response.raise_for_status()

                        output_dir = (
                            Path(__file__).parent
                            / "generated"
                        )

                        output_dir.mkdir(
                            exist_ok=True
                        )

                        output_path = (
                            output_dir / filename
                        )

                        with open(
                            output_path,
                            "wb"
                        ) as file:
                            file.write(
                                image_response.content
                            )

                        return str(output_path)

            time.sleep(1)

        raise TimeoutError(
            "ComfyUI image generation timed out."
        )