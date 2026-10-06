"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Plus, Trash2, Volume2 } from "lucide-react";

import { speak } from "@/lib/speak";
import { api, getToken, Level, VocabularyItem } from "@/services/api";

export default function AdminVocabularyPage() {
  const router = useRouter();
  const [levels, setLevels] = useState<Level[]>([]);
  const [levelId, setLevelId] = useState<number | null>(null);
  const [words, setWords] = useState<VocabularyItem[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ word_en: "", word_ru: "", transcription: "", image_url: "" });

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
        return api.levels();
      })
      .then((lv) => {
        if (!lv) return;
        setLevels(lv);
        if (lv.length > 0) setLevelId(lv[0].id);
      })
      .catch((e) => setError(e.message));
  }, [router]);

  async function loadWords(id: number) {
    setBusy(true);
    try {
      setWords(await api.levelVocabulary(id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (levelId != null) void loadWords(levelId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levelId]);

  async function addWord() {
    if (levelId == null || !form.word_en || !form.word_ru) return;
    setBusy(true);
    setError("");
    try {
      await api.createVocabulary(levelId, {
        word_en: form.word_en,
        word_ru: form.word_ru,
        transcription: form.transcription || null,
        image_url: form.image_url || null,
      });
      setForm({ word_en: "", word_ru: "", transcription: "", image_url: "" });
      await loadWords(levelId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function saveWord(w: VocabularyItem, patch: Partial<VocabularyItem>) {
    setBusy(true);
    setError("");
    try {
      await api.updateVocabulary(w.id, patch);
      if (levelId != null) await loadWords(levelId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function removeWord(id: number) {
    setBusy(true);
    try {
      await api.deleteVocabulary(id);
      if (levelId != null) await loadWords(levelId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-wide">
      <Link href="/admin/missions" className="eq-back">
        <ArrowLeft size={16} /> Missions
      </Link>

      <h1 className="eq-h1 mt-6">Vocabulary</h1>
      <p className="eq-sub">Manage the word pool used by the pronunciation and game modules.</p>

      <label className="mt-6 grid max-w-xs gap-1.5">
        <span className="eq-label">Level</span>
        <select
          className="eq-input"
          value={levelId ?? ""}
          onChange={(e) => setLevelId(Number(e.target.value))}
        >
          {levels.map((l) => (
            <option key={l.id} value={l.id}>
              {l.code} — {l.title}
            </option>
          ))}
        </select>
      </label>

      <section className="eq-card mt-6">
        <h2 className="eq-h2">Add word</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="grid gap-1.5">
            <span className="eq-label">English</span>
            <input
              className="eq-input"
              value={form.word_en}
              onChange={(e) => setForm({ ...form, word_en: e.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Перевод</span>
            <input
              className="eq-input"
              value={form.word_ru}
              onChange={(e) => setForm({ ...form, word_ru: e.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Транскрипция (opt.)</span>
            <input
              className="eq-input"
              placeholder="/ˈæp.əl/"
              value={form.transcription}
              onChange={(e) => setForm({ ...form, transcription: e.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Image URL (opt.)</span>
            <input
              className="eq-input"
              placeholder="/images/apple.svg"
              value={form.image_url}
              onChange={(e) => setForm({ ...form, image_url: e.target.value })}
            />
          </label>
        </div>
        {error && <p className="eq-caption mt-3 accent">{error}</p>}
        <div className="mt-4 flex items-center gap-3">
          <button className="btn-eq" disabled={busy || !form.word_en || !form.word_ru} onClick={addWord}>
            <Plus size={16} /> Add word
          </button>
          <button
            className="btn-eq-ghost"
            type="button"
            disabled={!form.word_en}
            onClick={() => speak(form.word_en)}
          >
            <Volume2 size={16} /> Listen
          </button>
          <span className="eq-caption">Sound is generated by the browser — no audio files needed.</span>
        </div>
      </section>

      <div className="mt-8 overflow-x-auto" style={{ border: "1px solid var(--eq-border)", borderRadius: 14 }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="eq-label" style={{ textAlign: "left", borderBottom: "1px solid var(--eq-border)" }}>
              <th className="p-3" style={{ fontWeight: 400 }}>English</th>
              <th className="p-3" style={{ fontWeight: 400 }}>Перевод</th>
              <th className="p-3" style={{ fontWeight: 400 }}>Транскрипция</th>
              <th className="p-3" style={{ fontWeight: 400 }}>Image URL</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {words.map((w) => (
              <WordRow key={w.id} word={w} busy={busy} onSave={saveWord} onDelete={removeWord} />
            ))}
            {words.length === 0 && (
              <tr>
                <td className="p-3 muted" colSpan={5}>
                  No words for this level yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function WordRow({
  word,
  busy,
  onSave,
  onDelete,
}: {
  word: VocabularyItem;
  busy: boolean;
  onSave: (w: VocabularyItem, patch: Partial<VocabularyItem>) => void;
  onDelete: (id: number) => void;
}) {
  const [en, setEn] = useState(word.word_en);
  const [ru, setRu] = useState(word.word_ru);
  const [tr, setTr] = useState(word.transcription ?? "");
  const [img, setImg] = useState(word.image_url ?? "");

  return (
    <tr style={{ borderTop: "1px solid var(--eq-border)" }}>
      <td className="p-2">
        <input className="eq-input" value={en} onChange={(e) => setEn(e.target.value)} />
      </td>
      <td className="p-2">
        <input className="eq-input" value={ru} onChange={(e) => setRu(e.target.value)} />
      </td>
      <td className="p-2">
        <input className="eq-input" value={tr} onChange={(e) => setTr(e.target.value)} />
      </td>
      <td className="p-2">
        <input className="eq-input" value={img} onChange={(e) => setImg(e.target.value)} />
      </td>
      <td className="p-2">
        <div className="flex items-center gap-2">
          <button className="muted" onClick={() => speak(en)} aria-label="Listen" title="Listen">
            <Volume2 size={16} />
          </button>
          <button
            className="btn-eq-ghost"
            disabled={busy}
            onClick={() =>
              onSave(word, {
                word_en: en,
                word_ru: ru,
                transcription: tr || null,
                image_url: img || null,
              })
            }
          >
            Save
          </button>
          <button className="muted" disabled={busy} onClick={() => onDelete(word.id)} aria-label="Delete">
            <Trash2 size={15} />
          </button>
        </div>
      </td>
    </tr>
  );
}
