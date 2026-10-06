from pydantic import BaseModel, Field, model_validator


class _GameScore(BaseModel):
    correctAnswers: int = Field(ge=0)
    totalQuestions: int = Field(gt=0)

    @model_validator(mode="after")
    def correct_not_exceed_total(self):
        if self.correctAnswers > self.totalQuestions:
            raise ValueError("correctAnswers cannot exceed totalQuestions")
        return self


class SubmitGameRequest(_GameScore):
    pass


class SubmitTestsRequest(_GameScore):
    pass
