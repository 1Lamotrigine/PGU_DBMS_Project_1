"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Plus, Trash2, ChevronRight } from "lucide-react";

import { api, Level, UserProfile } from "@/services/api";

export default function AdminMissionsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [levels, setLevels] = useState<Level[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ level_id: 1, order_index: 1, title: "", description: "" });

  const reload = () => api.levels().then(setLevels).catch((e) => setError(e.message));

  useEffect(() => {
    api
      .me()
      .then((me) => {
        if (me.role !== "teacher") {
          router.replace("/dashboard");
          return;
        }
        setProfile(me);
        return reload();
      })
      .catch((e) => setError(e.message));
  }, [router]);

  async function create() {
    setError("");
    try {
      await api.createMission({
        level_id: Number(form.level_id),
        order_index: Number(form.order_index),
        title: form.title,
        description: form.description,
        tasks: [{ title: "Vocabulary", task_type: "multiple_choice", xp_reward_first: 100, xp_reward_repeat: 10 }],
      });
      setForm({ ...form, title: "", description: "" });
      await reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove(id: number) {
    try {
      await api.deleteMission(id);
      await reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!profile) return <main className="page muted">Checking access…</main>;

  return (
    <main className="page-wide">
      <h1 className="eq-h1">Missions</h1>
      <p className="eq-sub">Manage missions, tasks, questions and vocabulary.</p>
      <div className="mt-4 flex gap-3">
        <Link href="/admin/vocabulary" className="btn-eq-ghost">
          Vocabulary
        </Link>
      </div>

      <section className="eq-card mt-8">
        <h2 className="eq-h2">New mission</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="grid gap-1.5">
            <span className="eq-label">Level</span>
            <select
              className="eq-input"
              value={form.level_id}
              onChange={(e) => setForm({ ...form, level_id: Number(e.target.value) })}
            >
              {levels.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.code} — {l.title}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Order</span>
            <select
              className="eq-input"
              value={form.order_index}
              onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Title</span>
            <input className="eq-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Description</span>
            <input
              className="eq-input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
        </div>
        {error && <p className="eq-caption mt-3" style={{ color: "var(--eq-text)" }}>{error}</p>}
        <button className="btn-eq mt-4" disabled={!form.title} onClick={create}>
          <Plus size={16} /> Create mission
        </button>
      </section>

      <div className="mt-8 grid gap-6">
        {levels.map((level) => (
          <section key={level.id}>
            <h2 className="eq-h2 mb-3">
              {level.code} <span className="eq-caption">· {level.missions.length}/5 missions</span>
            </h2>
            <div className="overflow-x-auto" style={{ border: "1px solid var(--eq-border)", borderRadius: 14 }}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="eq-label" style={{ textAlign: "left", borderBottom: "1px solid var(--eq-border)" }}>
                    <th className="p-3" style={{ fontWeight: 400 }}>#</th>
                    <th className="p-3" style={{ fontWeight: 400 }}>Title</th>
                    <th className="p-3" style={{ fontWeight: 400 }}>Tasks</th>
                    <th className="p-3" style={{ fontWeight: 400 }}>First XP</th>
                    <th className="p-3" style={{ fontWeight: 400 }}>Repeat XP</th>
                    <th className="p-3" />
                  </tr>
                </thead>
                <tbody>
                  {level.missions.map((m) => {
                    const first = m.tasks.reduce((s, t) => s + t.xp_reward_first, 0);
                    const repeat = m.tasks.reduce((s, t) => s + t.xp_reward_repeat, 0);
                    return (
                      <tr key={m.id} style={{ borderTop: "1px solid var(--eq-border)" }}>
                        <td className="p-3" style={{ fontWeight: 500 }}>{m.order_index}</td>
                        <td className="p-3">
                          <Link href={`/admin/missions/${m.id}`} className="accent font-medium">
                            {m.title}
                          </Link>
                        </td>
                        <td className="p-3">{m.tasks.length}</td>
                        <td className="p-3">{first}</td>
                        <td className="p-3">{repeat}</td>
                        <td className="p-3">
                          <div className="flex items-center justify-end gap-3">
                            <Link href={`/admin/missions/${m.id}`} className="muted" aria-label="Open">
                              <ChevronRight size={16} />
                            </Link>
                            <button className="muted" onClick={() => remove(m.id)} aria-label="Delete">
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}
