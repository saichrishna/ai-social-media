import uuid
from pathlib import Path

from image_generation.comfyui_service import ComfyUIService
from services.supabase_storage_service import SupabaseStorageService


class MediaGenerationService:

    def __init__(self):
        self.comfyui = ComfyUIService()
        self.storage = SupabaseStorageService()

    def generate_post_image(
        self,
        post_id: str,
        prompt: str
    ) -> dict:

        if not prompt or not prompt.strip():
            raise ValueError(
                "Image prompt is empty."
            )

        # -----------------------------------
        # 1. Generate image with ComfyUI
        # -----------------------------------

        local_path = self.comfyui.generate_image(
            prompt=prompt
        )

        # -----------------------------------
        # 2. Build unique Storage path
        # -----------------------------------

        filename = Path(local_path).name

        storage_path = (
            f"generated/"
            f"{post_id}/"
            f"{uuid.uuid4()}_{filename}"
        )

        # -----------------------------------
        # 3. Upload to Supabase Storage
        # -----------------------------------

        uploaded_path = self.storage.upload_image(
            local_path=local_path,
            storage_path=storage_path
        )

        return {
            "type": "image",
            "local_path": local_path,
            "storage_path": uploaded_path
        }