"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getToken } from "@/services/api";

export default function HomePage() {
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  return (
    <main className="page" style={{ paddingTop: 96 }}>
      <h1 className="eq-h1" style={{ fontSize: 40, maxWidth: 560 }}>
        Learn English by speaking it
      </h1>
      <p className="eq-sub" style={{ maxWidth: 520 }}>
        Placement test, CEFR levels from A0 to C2, and short spoken missions. Speak words out loud,
        clear the falling Russian words, and collect XP.
      </p>

      <div className="mt-10 flex gap-3">
        {authed ? (
          <Link href="/dashboard" className="btn-eq">
            Go to dashboard
          </Link>
        ) : (
          <>
            <Link href="/register" className="btn-eq">
              Get started
            </Link>
            <Link href="/login" className="btn-eq-ghost">
              Log in
            </Link>
          </>
        )}
      </div>

      <div className="mt-20 grid gap-10 md:grid-cols-3">
        <Feature title="Placement test" text="Find your CEFR level from A0 to C2 in a few minutes." />
        <Feature title="Levels & missions" text="Five focused missions per level, in a clear progression." />
        <Feature title="Speak to score" text="Say words out loud and get instant feedback." />
      </div>
    </main>
  );
}

function Feature({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <h2 className="eq-h2">{title}</h2>
      <p className="eq-caption mt-2">{text}</p>
    </div>
  );
}
