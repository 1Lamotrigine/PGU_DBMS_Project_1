from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="group")


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))

    missions: Mapped[list["Mission"]] = relationship(back_populates="level")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(5), default="A1")
    level_id: Mapped[int | None] = mapped_column(ForeignKey("levels.id"), nullable=True)
    # Highest level rank (index into CEFR_ORDER) the student has unlocked.
    unlocked_level_rank: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="users")
    group: Mapped["Group | None"] = relationship(back_populates="users")
    progress: Mapped[list["UserMissionProgress"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint("cefr_level IN ('A1','A2','B1','B2','C1','C2')", name="ck_users_cefr_level"),
    )


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"))
    order_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    level: Mapped["Level"] = relationship(back_populates="missions")
    tasks: Mapped[list["Task"]] = relationship(back_populates="mission", cascade="all, delete-orphan")
    progress: Mapped[list["UserMissionProgress"]] = relationship(back_populates="mission")

    __table_args__ = (
        CheckConstraint("order_index BETWEEN 1 AND 5", name="ck_missions_order_index"),
        UniqueConstraint("level_id", "order_index", name="uq_missions_level_order"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, default=1)
    time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xp_reward_first: Mapped[int] = mapped_column(Integer, default=100)
    xp_reward_repeat: Mapped[int] = mapped_column(Integer, default=10)

    mission: Mapped["Mission"] = relationship(back_populates="tasks")
    questions: Mapped[list["Question"]] = relationship(back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('vocabulary_game','multiple_choice','translation')",
            name="ck_tasks_task_type",
        ),
        CheckConstraint("xp_reward_first > 0", name="ck_tasks_xp_first"),
        CheckConstraint("xp_reward_repeat >= 0", name="ck_tasks_xp_repeat"),
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('multiple_choice','fill_blank','translation','image_match')",
            name="ck_questions_question_type",
        ),
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    translation_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    question: Mapped["Question"] = relationship(back_populates="options")


class CalibrationQuestion(Base):
    __tablename__ = "calibration_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(5), nullable=False)
    option_a: Mapped[str] = mapped_column(String(255), nullable=False)
    option_b: Mapped[str] = mapped_column(String(255), nullable=False)
    option_c: Mapped[str] = mapped_column(String(255), nullable=False)
    option_d: Mapped[str] = mapped_column(String(255), nullable=False)
    correct_option: Mapped[str] = mapped_column(String(1), nullable=False)

    __table_args__ = (
        CheckConstraint("cefr_level IN ('A1','A2','B1','B2','C1','C2')", name="ck_calib_cefr_level"),
        CheckConstraint("correct_option IN ('A','B','C','D')", name="ck_calib_correct_option"),
    )


class VocabularyItem(Base):
    """Word pairs for the 'Dictionary' arcade game (RU prompt -> EN answer)."""

    __tablename__ = "vocabulary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"), index=True)
    word_en: Mapped[str] = mapped_column(String(255), nullable=False)
    word_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    transcription: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class UserMissionProgress(Base):
    __tablename__ = "user_mission_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    tests_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    pronunciation_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    best_score_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    completion_count: Mapped[int] = mapped_column(Integer, default=0)
    # Total XP earned on this mission (sum across completed attempts).
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="progress")
    mission: Mapped["Mission"] = relationship(back_populates="progress")

    __table_args__ = (UniqueConstraint("user_id", "mission_id", name="uq_progress_user_mission"),)


class MissionAttempt(Base):
    """A single server-tracked run of a mission module.

    Attempts make rewards idempotent: each attempt can be completed exactly once,
    and XP is awarded per completed attempt rather than per raw request.
    """

    __tablename__ = "mission_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    module: Mapped[str] = mapped_column(String(20), default="game")  # test|pronunciation|game
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    # JSON list of the item/question ids issued to the client for this attempt.
    issued: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship()
    mission: Mapped["Mission"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress','completed','failed')",
            name="ck_attempt_status",
        ),
        CheckConstraint(
            "module IN ('test','pronunciation','game')",
            name="ck_attempt_module",
        ),
    )

