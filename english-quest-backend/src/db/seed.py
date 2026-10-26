from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.models.models import (
    CalibrationQuestion,
    Level,
    Mission,
    Question,
    QuestionOption,
    Role,
    Task,
    User,
    VocabularyItem,
)
from src.services.security import hash_password

LEVELS = [
    ("A1", "Beginner"),
    ("A2", "Elementary"),
    ("B1", "Intermediate"),
    ("B2", "Upper Intermediate"),
    ("C1", "Advanced"),
    ("C2", "Proficiency"),
]

CALIBRATION = {
    "A1": [
        ("She ___ from Spain.", "am", "is", "are", "be", "B"),
        ("There ___ two cats on the sofa.", "is", "are", "be", "was", "B"),
        ("I ___ coffee every morning.", "drink", "drinks", "drinking", "drank", "A"),
        ("This is my sister. ___ name is Emma.", "His", "Her", "Its", "Their", "B"),
    ],
    "A2": [
        ("We ___ to the beach last weekend.", "go", "went", "gone", "going", "B"),
        ("This exam is ___ than the last one.", "difficult", "more difficult", "most difficult", "difficulty", "B"),
        ("I've lived here ___ three years.", "since", "for", "from", "during", "B"),
        ("You ___ smoke here. It's forbidden.", "mustn't", "don't have to", "needn't", "shouldn't have", "A"),
    ],
    "B1": [
        ("By the time we arrived, the film ___ already ___.", "has / started", "had / started", "was / starting", "have / started", "B"),
        ("She's the woman ___ car was stolen.", "who", "which", "whose", "whom", "C"),
        ("I wish I ___ more time to study.", "have", "had", "will have", "would have", "B"),
        ("He suggested ___ the meeting until Friday.", "to postpone", "postponing", "postpone", "postponed", "B"),
    ],
    "B2": [
        ("Hardly ___ the office when it started raining.", "I had left", "had I left", "I left", "did I leave", "B"),
        ("If she ___ harder, she would have passed.", "studied", "had studied", "studies", "would study", "B"),
        ("I'd rather you ___ tell anyone about this.", "don't", "didn't", "haven't", "won't", "B"),
        ("The manager made us ___ the report twice.", "to rewrite", "rewriting", "rewrite", "rewrote", "C"),
    ],
    "C1": [
        ("___ had she finished speaking than the audience erupted.", "No sooner", "Hardly", "Scarcely", "Only when", "A"),
        ("The evidence is far from ___ conclusive.", "being", "be", "been", "to be", "A"),
        ("It was such a compelling argument that few could ___ it.", "refute", "refuse", "refund", "refuel", "A"),
        ("He tends to ___ the point rather than answer directly.", "evade", "invade", "pervade", "cascade", "A"),
        ("Were it not ___ your help, we would have failed.", "for", "of", "to", "with", "A"),
    ],
    "C2": [
        ("His remarks were so ___ that no one could pin down his real position.", "equivocal", "equitable", "equivalent", "unequivocal", "A"),
        ("The report was criticised for being ___ and full of contradictions.", "incoherent", "cohesive", "concise", "consistent", "A"),
        ("She has an ___ capacity for remembering names and faces.", "uncanny", "uncaring", "uncouth", "uncommon", "A"),
        ("The two theories, though different, are not mutually ___.", "exclusive", "exclusionary", "excluded", "excluding", "A"),
    ],
}

DICTIONARY_TASK = ("Dictionary game", "vocabulary_game", 120, 12)
GRAMMAR_TASK = ("Grammar", "grammar", 130, 13)

# EN word -> RU translation + picture, used by the test/pronunciation/dictionary.
VOCAB = [
    ("apple", "яблоко", "https://placehold.co/160x160?text=apple"),
    ("book", "книга", "https://placehold.co/160x160?text=book"),
    ("car", "машина", "https://placehold.co/160x160?text=car"),
    ("house", "дом", "https://placehold.co/160x160?text=house"),
    ("water", "вода", "https://placehold.co/160x160?text=water"),
]

# 5 meaningful multiple-choice questions per mission (A1 demo content).
TEST_QUESTIONS = [
    {
        "text": "Which word means «яблоко»?",
        "correct": "apple",
        "options": ["apple", "book", "car", "water"],
    },
    {
        "text": "Which word means «книга»?",
        "correct": "book",
        "options": ["house", "book", "apple", "water"],
    },
    {
        "text": "Which word means «машина»?",
        "correct": "car",
        "options": ["apple", "water", "car", "book"],
    },
    {
        "text": "Which word means «дом»?",
        "correct": "house",
        "options": ["house", "car", "book", "apple"],
    },
    {
        "text": "Which word means «вода»?",
        "correct": "water",
        "options": ["water", "apple", "house", "car"],
    },
]

# Words pronounced in the pronunciation module (EN + RU translation).
PRONUNCIATION_WORDS = [
    ("apple", "яблоко"),
    ("book", "книга"),
    ("car", "машина"),
    ("house", "дом"),
    ("water", "вода"),
]

# Grammar game: the prompt has a gap, the four flying cards are forms of the
# same word and the student clicks the correct one (no microphone needed).
GRAMMAR_QUESTIONS = [
    {
        "text": "She ___ guitar every day.",
        "correct": "plays",
        "options": ["play", "plays", "playing", "played"],
    },
    {
        "text": "They ___ to school by bus.",
        "correct": "go",
        "options": ["go", "goes", "going", "went"],
    },
    {
        "text": "He ___ breakfast at 7 o'clock.",
        "correct": "has",
        "options": ["have", "has", "having", "had"],
    },
    {
        "text": "She ___ her homework yesterday.",
        "correct": "did",
        "options": ["do", "does", "did", "doing"],
    },
    {
        "text": "There ___ a cat under the table.",
        "correct": "is",
        "options": ["is", "are", "am", "be"],
    },
    {
        "text": "My friends ___ football on Sundays.",
        "correct": "play",
        "options": ["play", "plays", "playing", "played"],
    },
    {
        "text": "We ___ watching TV now.",
        "correct": "are",
        "options": ["is", "am", "are", "be"],
    },
    {
        "text": "It ___ raining when we left.",
        "correct": "was",
        "options": ["is", "are", "am", "was"],
    },
    {
        "text": "You ___ speak English very well.",
        "correct": "can",
        "options": ["can", "cans", "could", "to can"],
    },
    {
        "text": "I ___ coffee every morning.",
        "correct": "drink",
        "options": ["drink", "drinks", "drinking", "drank"],
    },
]

# Per-level dictionary pool (RU prompt -> EN answer).
VOCABULARY = {
    "A1": [
        ("apple", "яблоко", "/ˈæp.əl/"),
        ("book", "книга", "/bʊk/"),
        ("car", "машина", "/kɑːr/"),
        ("house", "дом", "/haʊs/"),
        ("water", "вода", "/ˈwɔː.tər/"),
        ("dog", "собака", "/dɒɡ/"),
        ("cat", "кошка", "/kæt/"),
        ("sun", "солнце", "/sʌn/"),
        ("milk", "молоко", "/mɪlk/"),
        ("bread", "хлеб", "/bred/"),
        ("fish", "рыба", "/fɪʃ/"),
        ("tree", "дерево", "/triː/"),
        ("bird", "птица", "/bɜːd/"),
        ("door", "дверь", "/dɔːr/"),
        ("ball", "мяч", "/bɔːl/"),
    ],
    "A2": [
        ("weather", "погода", "/ˈweð.ər/"), ("holiday", "отпуск", "/ˈhɒl.ə.deɪ/"),
        ("market", "рынок", "/ˈmɑː.kɪt/"), ("letter", "письмо", "/ˈlet.ər/"),
        ("window", "окно", "/ˈwɪn.dəʊ/"), ("bridge", "мост", "/brɪdʒ/"),
        ("forest", "лес", "/ˈfɒr.ɪst/"), ("river", "река", "/ˈrɪv.ər/"),
        ("village", "деревня", "/ˈvɪl.ɪdʒ/"), ("island", "остров", "/ˈaɪ.lənd/"),
    ],
    "B1": [
        ("decision", "решение", "/dɪˈsɪʒ.ən/"), ("knowledge", "знание", "/ˈnɒl.ɪdʒ/"),
        ("research", "исследование", "/rɪˈsɜːtʃ/"), ("advantage", "преимущество", "/ədˈvɑːn.tɪdʒ/"),
        ("opinion", "мнение", "/əˈpɪn.jən/"), ("purpose", "цель", "/ˈpɜː.pəs/"),
        ("effort", "усилие", "/ˈef.ət/"), ("environment", "окружающая среда", "/ɪnˈvaɪ.rən.mənt/"),
        ("experience", "опыт", "/ɪkˈspɪə.ri.əns/"), ("opportunity", "возможность", "/ˌɒp.əˈtjuː.nə.ti/"),
    ],
    "B2": [
        ("approach", "подход", "/əˈprəʊtʃ/"), ("consequence", "последствие", "/ˈkɒn.sɪ.kwəns/"),
        ("estimate", "оценка", "/ˈes.tɪ.meɪt/"), ("evidence", "доказательство", "/ˈev.ɪ.dəns/"),
        ("impact", "влияние", "/ˈɪm.pækt/"), ("issue", "проблема", "/ˈɪʃ.uː/"),
        ("maintain", "поддерживать", "/meɪnˈteɪn/"), ("obtain", "получать", "/əbˈteɪn/"),
        ("relevant", "соответствующий", "/ˈrel.ə.vənt/"), ("significant", "значительный", "/sɪɡˈnɪf.ɪ.kənt/"),
    ],
    "C1": [
        ("ambiguous", "двусмысленный", "/æmˈbɪɡ.ju.əs/"), ("coherent", "связный", "/kəʊˈhɪə.rənt/"),
        ("comprehensive", "всеобъемлющий", "/ˌkɒm.prɪˈhen.sɪv/"), ("inevitable", "неизбежный", "/ɪnˈev.ɪ.tə.bəl/"),
        ("perceive", "воспринимать", "/pəˈsiːv/"), ("profound", "глубокий", "/prəˈfaʊnd/"),
        ("reluctant", "неохотный", "/rɪˈlʌk.tənt/"), ("subtle", "тонкий", "/ˈsʌt.əl/"),
        ("sustain", "поддерживать", "/səˈsteɪn/"), ("versatile", "универсальный", "/ˈvɜː.sə.taɪl/"),
    ],
    "C2": [
        ("ephemeral", "мимолётный", "/ɪˈfem.ər.əl/"), ("idiosyncratic", "своеобразный", "/ˌɪd.i.ə.sɪŋˈkræt.ɪk/"),
        ("ubiquitous", "вездесущий", "/juːˈbɪk.wɪ.təs/"), ("quintessential", "типичный", "/ˌkwɪn.tɪˈsen.ʃəl/"),
        ("pragmatic", "прагматичный", "/præɡˈmæt.ɪk/"), ("nuance", "нюанс", "/ˈnjuː.ɑːns/"),
        ("cohesive", "сплочённый", "/kəʊˈhiː.sɪv/"), ("formidable", "внушительный", "/fɔːˈmɪd.ə.bəl/"),
        ("lucid", "ясный", "/ˈluː.sɪd/"), ("scrutinize", "тщательно изучать", "/ˈskruː.tɪ.naɪz/"),
    ],
}

# Local images for the A1 word set (served from frontend/public/images/).
WORD_IMAGES = {
    "apple": "/images/apple.svg",
    "book": "/images/book.svg",
    "car": "/images/car.svg",
    "house": "/images/house.svg",
    "water": "/images/water.svg",
    "dog": "/images/dog.svg",
    "cat": "/images/cat.svg",
    "sun": "/images/sun.svg",
    "milk": "/images/milk.svg",
    "bread": "/images/bread.svg",
    "fish": "/images/fish.svg",
    "tree": "/images/tree.svg",
    "bird": "/images/bird.svg",
    "door": "/images/door.svg",
    "ball": "/images/ball.svg",
}


async def _get_or_create_role(db: AsyncSession, name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=name)
        db.add(role)
        await db.flush()
    return role


def _build_grammar_task(order_index: int) -> Task:
    """Fourth lesson stage: 5 grammar questions rotated per mission."""
    task = Task(
        title=GRAMMAR_TASK[0],
        task_type=GRAMMAR_TASK[1],
        order_number=4,
        xp_reward_first=GRAMMAR_TASK[2],
        xp_reward_repeat=GRAMMAR_TASK[3],
    )
    # Take five consecutive questions, wrapping around the pool.
    offset = (order_index - 1) * 2
    picked = [GRAMMAR_QUESTIONS[(offset + i) % len(GRAMMAR_QUESTIONS)] for i in range(5)]
    for item in picked:
        question = Question(question_text=item["text"], question_type="grammar_choice")
        for option in item["options"]:
            question.options.append(
                QuestionOption(
                    option_text=option,
                    is_correct=(option == item["correct"]),
                )
            )
        task.questions.append(question)
    return task


async def seed(db: AsyncSession) -> None:
    # Roles
    student_role = await _get_or_create_role(db, "student")
    teacher_role = await _get_or_create_role(db, "teacher")

    # Levels
    level_objects: dict[str, Level] = {}
    for code, title in LEVELS:
        result = await db.execute(select(Level).where(Level.code == code))
        level = result.scalar_one_or_none()
        if level is None:
            level = Level(code=code, title=title)
            db.add(level)
            await db.flush()
        level_objects[code] = level

    # In production we seed only roles and levels; demo content and the teacher
    # account are skipped unless SEED_DEMO=true.
    if not settings.SEED_DEMO:
        await db.commit()
        return

    # Calibration questions
    calib_count = await db.execute(select(func.count(CalibrationQuestion.id)))
    if int(calib_count.scalar_one()) == 0:
        for code, items in CALIBRATION.items():
            for text, a, b, c, d, correct in items:
                db.add(
                    CalibrationQuestion(
                        question_text=text,
                        cefr_level=code,
                        option_a=a,
                        option_b=b,
                        option_c=c,
                        option_d=d,
                        correct_option=correct,
                    )
                )

    # Vocabulary pool for the Dictionary game
    vocab_count = await db.execute(select(func.count(VocabularyItem.id)))
    if int(vocab_count.scalar_one()) == 0:
        for code, pairs in VOCABULARY.items():
            for word_en, word_ru, transcription in pairs:
                db.add(
                    VocabularyItem(
                        level_id=level_objects[code].id,
                        word_en=word_en,
                        word_ru=word_ru,
                        transcription=transcription,
                        image_url=WORD_IMAGES.get(word_en),
                    )
                )

    # Teacher account
    teacher_result = await db.execute(select(User).where(User.email == settings.TEACHER_EMAIL))
    if teacher_result.scalar_one_or_none() is None:
        db.add(
            User(
                first_name=settings.TEACHER_FIRST_NAME,
                last_name=settings.TEACHER_LAST_NAME,
                email=settings.TEACHER_EMAIL,
                password_hash=hash_password(settings.TEACHER_PASSWORD),
                role_id=teacher_role.id,
                is_calibrated=True,
                cefr_level="C2",
                level_id=level_objects["C2"].id,
            )
        )

    # Demo content: 5 missions for A1, each a 3-part lesson.
    a1 = level_objects["A1"]
    mission_count = await db.execute(select(func.count(Mission.id)).where(Mission.level_id == a1.id))
    if int(mission_count.scalar_one()) == 0:
        for index in range(1, 6):
            mission = Mission(
                level_id=a1.id,
                order_index=index,
                title=f"A1 Mission {index}",
                description=f"Beginner lesson number {index}",
            )

            # Part 1 — Test: 5 meaningful questions.
            test_task = Task(
                title="Test",
                task_type="multiple_choice",
                order_number=1,
                xp_reward_first=100,
                xp_reward_repeat=10,
            )
            for item in TEST_QUESTIONS:
                question = Question(question_text=item["text"], question_type="multiple_choice")
                for option_en in item["options"]:
                    translation = next((ru for en, ru, _ in VOCAB if en == option_en), None)
                    image_url = next((img for en, _, img in VOCAB if en == option_en), None)
                    question.options.append(
                        QuestionOption(
                            option_text=option_en,
                            translation_ru=translation,
                            is_correct=(option_en == item["correct"]),
                            image_url=image_url,
                        )
                    )
                test_task.questions.append(question)
            mission.tasks.append(test_task)

            # Part 2 — Pronunciation: say each English word.
            pron_task = Task(
                title="Pronunciation",
                task_type="translation",
                order_number=2,
                xp_reward_first=150,
                xp_reward_repeat=15,
            )
            for word_en, word_ru in PRONUNCIATION_WORDS:
                image_url = next((img for en, _, img in VOCAB if en == word_en), None)
                question = Question(
                    question_text=f"Say the English word for «{word_ru}»",
                    question_type="translation",
                )
                question.options.append(
                    QuestionOption(
                        option_text=word_en,
                        translation_ru=word_ru,
                        is_correct=True,
                        image_url=image_url,
                    )
                )
                pron_task.questions.append(question)
            mission.tasks.append(pron_task)

            # Part 3 — Dictionary game (RU prompt -> EN answer, timed).
            dict_task = Task(
                title=DICTIONARY_TASK[0],
                task_type=DICTIONARY_TASK[1],
                order_number=3,
                xp_reward_first=DICTIONARY_TASK[2],
                xp_reward_repeat=DICTIONARY_TASK[3],
            )
            mission.tasks.append(dict_task)

            # Part 4 — Grammar game (gap-fill prompt + four word forms).
            mission.tasks.append(_build_grammar_task(index))

            db.add(mission)

    # Existing installations already have the three-stage demo missions; add the
    # fourth stage without touching progress or XP.
    existing_missions = (
        await db.execute(
            select(Mission)
            .options(selectinload(Mission.tasks))
            .where(Mission.level_id == a1.id)
            .order_by(Mission.order_index)
        )
    ).scalars().all()
    for mission in existing_missions:
        if not any(task.task_type == "grammar" for task in mission.tasks):
            mission.tasks.append(_build_grammar_task(mission.order_index))

    # One transaction for the whole seed: roles, levels, content and accounts
    # are applied together or not at all.
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
