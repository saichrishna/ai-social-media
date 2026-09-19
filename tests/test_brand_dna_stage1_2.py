import sys
from types import ModuleType
from unittest.mock import MagicMock


def _stub_repo(module_name: str, class_name: str):

    module = ModuleType(module_name)
    setattr(module, class_name, MagicMock)
    sys.modules[module_name] = module


_stub_repo(
    "repositories.brand_profile_repository",
    "BrandProfileRepository"
)
_stub_repo(
    "repositories.voice_sample_repository",
    "VoiceSampleRepository"
)
_stub_repo(
    "repositories.interview_answer_repository",
    "InterviewAnswerRepository"
)

from fastapi import FastAPI
from fastapi.testclient import TestClient

from models.brand_profile_request import BrandProfileRequest
from models.interview_answer import InterviewAnswersSaveRequest
from models.voice_sample import VoiceSampleRequest
from utils.promise_completeness import promise_warnings

from routes import brand_profile_routes as brand_routes
from routes.brand_profile_routes import router


def _client():

    brand_routes.brand_repository = MagicMock()
    brand_routes.voice_sample_repository = MagicMock()
    brand_routes.interview_answer_repository = MagicMock()

    app = FastAPI()
    app.include_router(router)

    return TestClient(app)


LEGACY_CREATE_BODY = {
    "user_id": "user-1",
    "business_name": "Clinic",
    "industry": "Health"
}


def test_brand_profile_request_new_fields_default_empty():

    profile = BrandProfileRequest(
        user_id="user-1",
        business_name="Clinic",
        industry="Health"
    )

    dumped = profile.model_dump()

    assert dumped["not_for"] == ""
    assert dumped["desired_outcome"] == ""
    assert dumped["brand_voice"] == ""
    assert dumped["target_audience"] == ""


def test_brand_profile_request_accepts_stage1_fields():

    profile = BrandProfileRequest(
        user_id="user-1",
        business_name="Clinic",
        industry="Health",
        brand_voice="leftover",
        target_audience="new parents",
        not_for="enterprise HR teams",
        desired_outcome="more bookings"
    )

    assert profile.not_for == "enterprise HR teams"
    assert profile.desired_outcome == "more bookings"
    assert profile.brand_voice == "leftover"


def test_promise_warnings_when_audience_or_not_for_blank():

    warnings = promise_warnings({
        "target_audience": "  ",
        "not_for": ""
    })

    assert "target_audience is empty" in warnings
    assert "not_for is empty" in warnings


def test_promise_warnings_clear_when_fields_filled():

    warnings = promise_warnings({
        "target_audience": "new parents",
        "not_for": "enterprise"
    })

    assert warnings == []


def test_get_profile_attaches_warnings_and_does_not_400():

    client = _client()

    brand_routes.brand_repository.get_profile.return_value = [{
        "id": "brand-1",
        "user_id": "user-1",
        "business_name": "Clinic",
        "target_audience": "",
        "not_for": ""
    }]

    response = client.get("/brand-profiles/brand-1")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "target_audience is empty" in body["promise_warnings"]
    assert "not_for is empty" in body["promise_warnings"]


def test_get_user_profiles_attaches_warnings_per_row():

    client = _client()

    brand_routes.brand_repository.get_user_profiles.return_value = [
        {
            "id": "brand-1",
            "target_audience": "",
            "not_for": "not clinics"
        },
        {
            "id": "brand-2",
            "target_audience": "parents",
            "not_for": "enterprise"
        }
    ]

    response = client.get("/brand-profiles/user/user-1")

    assert response.status_code == 200
    profiles = response.json()["brand_profiles"]
    assert "target_audience is empty" in profiles[0]["promise_warnings"]
    assert profiles[1]["promise_warnings"] == []


def test_incomplete_create_does_not_400():

    client = _client()

    brand_routes.brand_repository.create_profile.return_value = [{
        "id": "brand-1",
        "not_for": "",
        "desired_outcome": ""
    }]

    response = client.post(
        "/brand-profiles/",
        json=LEGACY_CREATE_BODY
    )

    assert response.status_code == 200
    dumped = (
        brand_routes.brand_repository
        .create_profile
        .call_args
        .args[0]
    )
    assert dumped["not_for"] == ""
    assert dumped["desired_outcome"] == ""
    assert dumped["brand_voice"] == ""


def test_add_paste_and_audio_text_samples():

    client = _client()

    brand_routes.brand_repository.get_profile.return_value = [{
        "id": "brand-1",
        "user_id": "user-1"
    }]

    brand_routes.voice_sample_repository.create_sample.side_effect = [
        [{"id": "s1", "source": "paste", "content": "Real caption."}],
        [{"id": "s2", "source": "audio", "content": "Spoken transcript."}]
    ]

    paste = client.post(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"},
        json={
            "source": "paste",
            "content": "Real caption."
        }
    )

    audio = client.post(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"},
        json={
            "source": "audio",
            "content": "Spoken transcript."
        }
    )

    assert paste.status_code == 200
    assert audio.status_code == 200
    assert paste.json()["voice_sample"]["source"] == "paste"
    assert audio.json()["voice_sample"]["source"] == "audio"


def test_list_samples_scoped_to_user_and_brand():

    client = _client()

    brand_routes.brand_repository.get_profile.return_value = [{
        "id": "brand-1"
    }]

    brand_routes.voice_sample_repository.get_samples.return_value = [
        {"id": "s1"}
    ]

    response = client.get(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"}
    )

    assert response.status_code == 200
    (
        brand_routes.voice_sample_repository
        .get_samples
        .assert_called_once_with(
            brand_profile_id="brand-1",
            user_id="user-1"
        )
    )


def test_save_interview_answers_preserves_wording():

    client = _client()

    raw = "Customers think we only do 'sleep training' — we don't."

    brand_routes.brand_repository.get_profile.return_value = [{
        "id": "brand-1"
    }]

    brand_routes.interview_answer_repository.upsert_answers.return_value = [
        {
            "question_key": "customers_get_wrong",
            "answer_text": raw,
            "source": "type"
        }
    ]

    response = client.put(
        "/brand-profiles/brand-1/interview-answers",
        params={"user_id": "user-1"},
        json={
            "user_id": "user-1",
            "answers": [
                {
                    "question_key": "customers_get_wrong",
                    "question_text": "What do customers get wrong?",
                    "answer_text": raw,
                    "source": "type"
                }
            ]
        }
    )

    assert response.status_code == 200
    rows = (
        brand_routes.interview_answer_repository
        .upsert_answers
        .call_args
        .args[0]
    )
    assert rows[0]["answer_text"] == raw
    assert response.json()["interview_answers"][0]["answer_text"] == raw


def test_nested_routes_404_on_user_mismatch():

    client = _client()

    brand_routes.brand_repository.get_profile.return_value = []

    samples = client.get(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "other-user"}
    )

    answers = client.put(
        "/brand-profiles/brand-1/interview-answers",
        json={
            "user_id": "other-user",
            "answers": []
        }
    )

    assert samples.status_code == 404
    assert answers.status_code == 404
    brand_routes.brand_repository.get_profile.assert_any_call(
        "brand-1",
        "other-user"
    )


def test_reject_unknown_source_and_empty_content():

    client = _client()

    brand_routes.brand_repository.get_profile.return_value = [{
        "id": "brand-1"
    }]

    unknown = client.post(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"},
        json={
            "source": "scrape",
            "content": "hello"
        }
    )

    empty = client.post(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"},
        json={
            "source": "paste",
            "content": "   "
        }
    )

    unknown_answer = client.put(
        "/brand-profiles/brand-1/interview-answers",
        params={"user_id": "user-1"},
        json={
            "user_id": "user-1",
            "answers": [
                {
                    "question_key": "changed_my_mind",
                    "question_text": "What changed?",
                    "answer_text": "something",
                    "source": "llm"
                }
            ]
        }
    )

    assert unknown.status_code == 400
    assert empty.status_code == 400
    assert unknown_answer.status_code == 400


def test_reject_multipart_sample_upload():

    client = _client()

    response = client.post(
        "/brand-profiles/brand-1/samples",
        params={"user_id": "user-1"},
        files={
            "file": ("clip.wav", b"bytes", "audio/wav")
        }
    )

    assert response.status_code in {400, 422}


def test_voice_and_interview_models_keep_raw_fields():

    sample = VoiceSampleRequest(
        source="paste",
        content="Keep this caption."
    )

    payload = InterviewAnswersSaveRequest(
        user_id="user-1",
        answers=[
            {
                "question_key": "unpublished_advice",
                "question_text": "Advice never posted?",
                "answer_text": "Don't overnight wean.",
                "source": "audio"
            }
        ]
    )

    assert sample.content == "Keep this caption."
    assert payload.answers[0].answer_text == "Don't overnight wean."
