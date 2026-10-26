from pydantic import BaseModel, Field, model_validator


class AnswerItem(BaseModel):
    """A single answer to a mission test question (server grades it)."""

    question_id: int = Field(gt=0)
    option_id: int | None = Field(default=None, gt=0)
    text: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def one_answer(self):
        if (self.option_id is None) == (self.text is None):
            raise ValueError("Provide exactly one of option_id or text")
        return self


class WordAnswer(BaseModel):
    """A spoken/matched word for a vocabulary item (server grades it)."""

    item_id: int = Field(gt=0)
    word: str = Field(min_length=1, max_length=255)


class SubmitTestsRequest(BaseModel):
    """Server-graded test block. The client sends selected option ids only."""

    answers: list[AnswerItem] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_questions(self):
        ids = [a.question_id for a in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate question_id in answers")
        return self


class SubmitPronunciationRequest(BaseModel):
    """Pronunciation block. Preferred mode: server-graded word answers."""

    attempt_id: int | None = None
    answers: list[WordAnswer] | None = None

    # Legacy client-reported score (deprecated, kept for backward compatibility).
    correctAnswers: int | None = Field(default=None, ge=0)
    totalQuestions: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def one_mode(self):
        if not self.answers and self.correctAnswers is None:
            raise ValueError("Provide either answers or correctAnswers/totalQuestions")
        if self.correctAnswers is not None and self.totalQuestions is None:
            raise ValueError("totalQuestions is required with correctAnswers")
        return self


class SubmitGameRequest(BaseModel):
    """Arcade result. Preferred mode: server-graded word answers tied to an attempt."""

    attempt_id: int | None = None
    answers: list[WordAnswer] | None = None

    # Legacy client-reported score (deprecated, kept for backward compatibility).
    correctAnswers: int | None = Field(default=None, ge=0)
    totalQuestions: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def one_mode(self):
        if not self.answers and self.correctAnswers is None:
            raise ValueError("Provide either answers or correctAnswers/totalQuestions")
        if self.correctAnswers is not None:
            if self.totalQuestions is None:
                raise ValueError("totalQuestions is required with correctAnswers")
            if self.correctAnswers > self.totalQuestions:
                raise ValueError("correctAnswers cannot exceed totalQuestions")
        return self


class StartAttemptRequest(BaseModel):
    """Optionally select which module the attempt is for."""

    module: str = Field(default="game", pattern="^(test|pronunciation|game|grammar)$")


class GrammarAnswer(BaseModel):
    """One picked option for a grammar question (server grades it)."""

    question_id: int = Field(gt=0)
    option_id: int = Field(gt=0)


class SubmitGrammarRequest(BaseModel):
    """Grammar game result tied to a server-issued attempt."""

    attempt_id: int = Field(gt=0)
    answers: list[GrammarAnswer] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_questions(self):
        ids = [a.question_id for a in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate question_id in answers")
        return self


class CheckGrammarRequest(BaseModel):
    """One live answer check, so the game can give instant feedback."""

    question_id: int = Field(gt=0)
    option_id: int = Field(gt=0)
