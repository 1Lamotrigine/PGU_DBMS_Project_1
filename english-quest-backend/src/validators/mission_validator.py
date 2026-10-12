from pydantic import BaseModel, Field, field_validator, model_validator


# ---------- Tasks ----------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    task_type: str = Field(pattern="^(vocabulary_game|multiple_choice|translation)$")
    order_number: int = Field(default=1, ge=1)
    time_limit: int | None = Field(default=None, gt=0)
    xp_reward_first: int = Field(default=100, gt=0)
    xp_reward_repeat: int = Field(default=10, ge=0)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    task_type: str | None = Field(default=None, pattern="^(vocabulary_game|multiple_choice|translation)$")
    order_number: int | None = Field(default=None, ge=1)
    time_limit: int | None = Field(default=None, gt=0)
    xp_reward_first: int | None = Field(default=None, gt=0)
    xp_reward_repeat: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def no_null_required(self):
        for field in ("task_type", "order_number", "xp_reward_first", "xp_reward_repeat"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


# ---------- Questions ----------
class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: str = Field(
        default="multiple_choice",
        pattern="^(multiple_choice|fill_blank|translation|image_match)$",
    )


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=1)
    question_type: str | None = Field(
        default=None,
        pattern="^(multiple_choice|fill_blank|translation|image_match)$",
    )

    @model_validator(mode="after")
    def no_null_required(self):
        for field in ("question_type",):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


# ---------- Options ----------
class OptionCreate(BaseModel):
    option_text: str = Field(min_length=1)
    is_correct: bool = False
    image_url: str | None = Field(default=None, max_length=500)
    translation_ru: str | None = Field(default=None, max_length=255)


class OptionUpdate(BaseModel):
    option_text: str | None = Field(default=None, min_length=1)
    is_correct: bool | None = None
    image_url: str | None = Field(default=None, max_length=500)
    translation_ru: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def no_null_required(self):
        if "is_correct" in self.model_fields_set and self.is_correct is None:
            raise ValueError("is_correct cannot be null")
        return self


# ---------- Missions ----------
class MissionCreate(BaseModel):
    level_id: int = Field(gt=0)
    order_index: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    tasks: list[TaskCreate] = Field(default_factory=list)


class MissionUpdate(BaseModel):
    level_id: int | None = Field(default=None, gt=0)
    order_index: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def no_null_required(self):
        for field in ("level_id", "order_index", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


# ---------- Vocabulary ----------
class VocabularyCreate(BaseModel):
    word_en: str = Field(min_length=1, max_length=255)
    word_ru: str = Field(min_length=1, max_length=255)
    transcription: str | None = Field(default=None, max_length=255)
    image_url: str | None = Field(default=None, max_length=500)


class VocabularyUpdate(BaseModel):
    word_en: str | None = Field(default=None, min_length=1, max_length=255)
    word_ru: str | None = Field(default=None, min_length=1, max_length=255)
    transcription: str | None = Field(default=None, max_length=255)
    image_url: str | None = Field(default=None, max_length=500)
