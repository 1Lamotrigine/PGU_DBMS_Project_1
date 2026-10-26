"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Plus, Trash2, Volume2 } from "lucide-react";

import { speak } from "@/lib/speak";
import { api, getToken, Level, Mission, Question, QuestionOption, Task } from "@/services/api";

const TASK_TYPES = ["multiple_choice", "vocabulary_game", "translation", "grammar"];
const QUESTION_TYPES = ["multiple_choice", "fill_blank", "translation", "image_match", "grammar_choice"];

export default function MissionEditorPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);

  const [mission, setMission] = useState<Mission | null>(null);
  const [levels, setLevels] = useState<Level[]>([]);
  const [levelCode, setLevelCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const m = await api.mission(missionId);
    setMission(m);
    try {
      const lvls = await api.levels();
      setLevels(lvls);
      setLevelCode(lvls.find((l) => l.id === m.level_id)?.code ?? "");
    } catch {
      /* ignore */
    }
  }, [missionId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then((me) => {
        if (me.role !== "teacher") {
          router.replace("/dashboard");
          return;
        }
        return load();
      })
      .catch((e) => setError(e.message));
  }, [router, load]);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (error && !mission) return <main className="page accent">{error}</main>;
  if (!mission) return <main className="page muted">Loading…</main>;

  return (
    <main className="page-wide">
      <Link href="/admin/missions" className="eq-back">
        <ArrowLeft size={16} /> Missions
      </Link>

      <h1 className="eq-h1 mt-6">{mission.title}</h1>
      <p className="eq-sub">
        {levelCode ? `${levelCode} · ` : ""}Add tasks, questions and options.
      </p>

      {error && <p className="eq-caption mt-3 accent">{error}</p>}

      <MissionProperties mission={mission} levels={levels} busy={busy} run={run} />

      <div className="mt-8 grid gap-6">
        {mission.tasks.map((task) => (
          <TaskBlock key={task.id} task={task} busy={busy} run={run} />
        ))}
      </div>

      <button
        className="btn-eq mt-6"
        disabled={busy}
        onClick={() =>
          run(() =>
            api.createTask(missionId, {
              title: "New task",
              task_type: "multiple_choice",
              xp_reward_first: 100,
              xp_reward_repeat: 10,
            }),
          )
        }
      >
        <Plus size={16} /> Add task
      </button>
    </main>
  );
}

function MissionProperties({
  mission,
  levels,
  busy,
  run,
}: {
  mission: Mission;
  levels: Level[];
  busy: boolean;
  run: (fn: () => Promise<unknown>) => void;
}) {
  const [title, setTitle] = useState(mission.title);
  const [description, setDescription] = useState(mission.description ?? "");
  const [levelId, setLevelId] = useState(mission.level_id);
  const [orderIndex, setOrderIndex] = useState(mission.order_index);
  const [isActive, setIsActive] = useState(mission.is_active);

  return (
    <section className="eq-card mt-6">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1.5 sm:col-span-2">
          <span className="eq-label">Title</span>
          <input className="eq-input" value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className="grid gap-1.5 sm:col-span-2">
          <span className="eq-label">Description</span>
          <textarea
            className="eq-input"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Level</span>
          <select
            className="eq-input"
            value={levelId}
            onChange={(e) => setLevelId(Number(e.target.value))}
          >
            {levels.map((l) => (
              <option key={l.id} value={l.id}>
                {l.code}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Order (1–5)</span>
          <input
            type="number"
            min={1}
            max={5}
            className="eq-input"
            value={orderIndex}
            onChange={(e) => setOrderIndex(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          <span className="eq-label">Active (visible to students)</span>
        </label>
      </div>
      <button
        className="btn-eq mt-4"
        disabled={busy || title.trim().length === 0}
        onClick={() =>
          run(() =>
            api.updateMission(mission.id, {
              title: title.trim(),
              description: description || null,
              level_id: levelId,
              order_index: orderIndex,
              is_active: isActive,
            }),
          )
        }
      >
        Save mission
      </button>
    </section>
  );
}

function TaskBlock({
  task,
  busy,
  run,
}: {
  task: Task;
  busy: boolean;
  run: (fn: () => Promise<unknown>) => void;
}) {
  const [title, setTitle] = useState(task.title);
  const [taskType, setTaskType] = useState(task.type);
  const [xpFirst, setXpFirst] = useState(task.xp_reward_first);
  const [xpRepeat, setXpRepeat] = useState(task.xp_reward_repeat);

  return (
    <section className="eq-card">
      <div className="grid gap-3 sm:grid-cols-4">
        <label className="grid gap-1.5 sm:col-span-2">
          <span className="eq-label">Task title</span>
          <input className="eq-input" value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Type</span>
          <select className="eq-input" value={taskType} onChange={(e) => setTaskType(e.target.value)}>
            {TASK_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="grid gap-1.5">
            <span className="eq-label">XP first</span>
            <input
              type="number"
              className="eq-input"
              value={xpFirst}
              onChange={(e) => setXpFirst(Number(e.target.value))}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">XP repeat</span>
            <input
              type="number"
              className="eq-input"
              value={xpRepeat}
              onChange={(e) => setXpRepeat(Number(e.target.value))}
            />
          </label>
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          className="btn-eq-ghost"
          disabled={busy}
          onClick={() =>
            run(() =>
              api.updateTask(task.id, {
                title,
                task_type: taskType,
                xp_reward_first: xpFirst,
                xp_reward_repeat: xpRepeat,
              }),
            )
          }
        >
          Save task
        </button>
        <button
          className="muted flex items-center gap-1 px-3"
          disabled={busy}
          onClick={() => run(() => api.deleteTask(task.id))}
        >
          <Trash2 size={15} /> Delete
        </button>
      </div>

      <div className="mt-5 grid gap-4 border-l-2 pl-4" style={{ borderColor: "var(--eq-border)" }}>
        {(task.questions ?? []).map((q) => (
          <QuestionBlock key={q.id} question={q} busy={busy} run={run} />
        ))}
        <button
          className="btn-eq-ghost w-fit"
          disabled={busy}
          onClick={() =>
            run(() =>
              api.createQuestion(task.id, {
                question_text: "New question",
                question_type: taskType === "grammar" ? "grammar_choice" : "multiple_choice",
              }),
            )
          }
        >
          <Plus size={15} /> Add question
        </button>
      </div>
    </section>
  );
}

function QuestionBlock({
  question,
  busy,
  run,
}: {
  question: Question;
  busy: boolean;
  run: (fn: () => Promise<unknown>) => void;
}) {
  const [text, setText] = useState(question.question_text);
  const [type, setType] = useState(question.question_type);

  return (
    <div className="eq-card" style={{ background: "var(--eq-bg)" }}>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="grid gap-1.5 sm:col-span-2">
          <span className="eq-label">Question</span>
          <input className="eq-input" value={text} onChange={(e) => setText(e.target.value)} />
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Type</span>
          <select className="eq-input" value={type} onChange={(e) => setType(e.target.value)}>
            {QUESTION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="btn-eq-ghost"
          disabled={busy}
          onClick={() => run(() => api.updateQuestion(question.id, { question_text: text, question_type: type }))}
        >
          Save question
        </button>
        <button
          className="muted flex items-center gap-1 px-3"
          disabled={busy}
          onClick={() => run(() => api.deleteQuestion(question.id))}
        >
          <Trash2 size={15} /> Delete
        </button>
      </div>

      <div className="mt-4 grid gap-2">
        {question.options.map((o) => (
          <OptionRow key={o.id} option={o} busy={busy} run={run} />
        ))}
        <button
          className="btn-eq-ghost w-fit"
          disabled={busy}
          onClick={() => run(() => api.createOption(question.id, { option_text: "New option", is_correct: false }))}
        >
          <Plus size={15} /> Add option
        </button>
      </div>
    </div>
  );
}

function OptionRow({
  option,
  busy,
  run,
}: {
  option: QuestionOption;
  busy: boolean;
  run: (fn: () => Promise<unknown>) => void;
}) {
  const [text, setText] = useState(option.option_text);
  const [translation, setTranslation] = useState(option.translation_ru ?? "");
  const [imageUrl, setImageUrl] = useState(option.image_url ?? "");
  const [isCorrect, setIsCorrect] = useState(option.is_correct);

  return (
    <div
      className="grid items-end gap-2 sm:grid-cols-[1fr_1fr_1fr_auto_auto_auto]"
      style={{ borderBottom: "1px solid var(--eq-border)", paddingBottom: 8 }}
    >
      <label className="grid gap-1">
        <span className="eq-label">English</span>
        <input className="eq-input" value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      <label className="grid gap-1">
        <span className="eq-label">Перевод</span>
        <input className="eq-input" value={translation} onChange={(e) => setTranslation(e.target.value)} />
      </label>
      <label className="grid gap-1">
        <span className="eq-label">Image URL</span>
        <input
          className="eq-input"
          placeholder="/images/apple.svg"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
        />
      </label>
      <label className="flex items-center gap-2 pb-2" title="Correct answer">
        <input type="checkbox" checked={isCorrect} onChange={(e) => setIsCorrect(e.target.checked)} />
        <span className="eq-label">correct</span>
      </label>
      <button
        className="btn-eq-ghost"
        disabled={busy}
        onClick={() =>
          run(() =>
            api.updateOption(option.id, {
              option_text: text,
              translation_ru: translation || null,
              image_url: imageUrl || null,
              is_correct: isCorrect,
            }),
          )
        }
      >
        Save
      </button>
      <div className="flex gap-1">
        <button
          className="muted px-2 pb-2"
          onClick={() => speak(text)}
          disabled={!text}
          aria-label="Listen"
          title="Listen"
        >
          <Volume2 size={16} />
        </button>
        <button
          className="muted px-2 pb-2"
          disabled={busy}
          onClick={() => run(() => api.deleteOption(option.id))}
          aria-label="Delete option"
        >
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  );
}
