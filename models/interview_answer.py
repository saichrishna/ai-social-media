from pydantic import BaseModel, Field
from typing import List


# Canonical question_key values (client-supplied; API does not invent answers):
#   customers_get_wrong
#   changed_my_mind
#   unpublished_advice
#   customer_sentence
#   industry_disagree


class InterviewAnswerItem(BaseModel):

    question_key: str

    question_text: str = ""

    answer_text: str

    source: str


class InterviewAnswersSaveRequest(BaseModel):

    user_id: str = ""

    answers: List[InterviewAnswerItem] = Field(
        default_factory=list
    )
