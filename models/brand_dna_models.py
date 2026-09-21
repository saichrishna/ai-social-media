from pydantic import BaseModel, Field
from typing import List


class StartInterviewSessionRequest(BaseModel):

    user_id: str = ""

    cold_open_answer: str = ""

    mode: str = "full"


class InterviewAnswerStepRequest(BaseModel):

    user_id: str = ""

    question_key: str

    answer_text: str

    source: str = "type"


class CompleteInterviewSessionRequest(BaseModel):

    user_id: str = ""

    transcript: str = ""


class ChannelPreferenceRequest(BaseModel):

    user_id: str = ""

    platform: str

    tone_notes: str = ""

    length_notes: str = ""

    hashtag_notes: str = ""


class DraftGenerateRequest(BaseModel):

    user_id: str

    topic: str

    platform: str = "instagram"

    description: str = ""
