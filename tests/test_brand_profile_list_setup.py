import sys
from types import ModuleType
from unittest.mock import MagicMock


def _stub_repo(module_name: str, class_name: str):

    module = ModuleType(module_name)
    setattr(module, class_name, MagicMock)
    sys.modules[module_name] = module


_stub_repo(
    "repositories.brand_profile_repository",
    "BrandProfileRepository",
)
_stub_repo(
    "repositories.voice_sample_repository",
    "VoiceSampleRepository",
)
_stub_repo(
    "repositories.interview_answer_repository",
    "InterviewAnswerRepository",
)
_stub_repo(
    "repositories.interview_session_repository",
    "InterviewSessionRepository",
)

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import brand_profile_routes as brand_routes
from routes.brand_profile_routes import router


def _client():

    brand_routes.brand_repository = MagicMock()
    brand_routes.voice_sample_repository = MagicMock()
    brand_routes.interview_answer_repository = MagicMock()

    app = FastAPI()
    app.include_router(router)

    return TestClient(app)


def test_user_brand_list_includes_setup_summary():

    client = _client()

    brand_routes.brand_repository.get_user_profiles.return_value = [
        {
            "id": "brand-1",
            "user_id": "user-1",
            "business_name": "Clinic",
            "target_audience": "Parents",
            "not_for": "Kids",
        }
    ]
    brand_routes.voice_sample_repository.list_content_by_user.return_value = [
        {
            "brand_profile_id": "brand-1",
            "content": "one",
        },
        {
            "brand_profile_id": "brand-1",
            "content": "two",
        },
    ]
    brand_routes.interview_answer_repository.list_content_by_user.return_value = [
        {
            "brand_profile_id": "brand-1",
            "answer_text": "three",
        },
    ]

    response = client.get("/brand-profiles/user/user-1")

    assert response.status_code == 200
    profile = response.json()["brand_profiles"][0]
    assert profile["setup_status"] == "ready_to_draft"
    assert profile["material_count"] == 3
    assert profile["draft_ready"] is True
