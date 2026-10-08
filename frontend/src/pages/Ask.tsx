import { SendHorizontal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { AskResponse } from "../api/client";
import { useAsk } from "../api/hooks";
import { Warming } from "../components/StateViews";

const SUGGESTIONS = [
  "Which stores will run out of generators this week?",
  "Which stores have extra stock?",
  "Which transfers are urgent?",
  "Which stores will run out of tarps?",
];

type Turn = { question: string; reply?: AskResponse; failed?: string };

function Answer({ r }: { r: AskResponse }) {
  return (
    <div className="max-w-full rounded-2xl rounded-tl-md bg-paper p-4 shadow-[0_1px_0_var(--color-line)]">
      <p className="font-semibold">{r.answer}</p>
      {r.table && (
        <div className="mt-3 overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-max text-left text-sm tabular-nums">
            <caption className="sr-only">Answer details</caption>
            <thead className="bg-mist">
              <tr>
                {r.table.columns.map((c) => (
                  <th key={c} scope="col" className="px-3 py-2 font-extrabold">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.table.rows.map((row, i) => (
                <tr key={i} className="border-t border-line">
                  {row.map((cell, j) => (
                    <td key={j} className={`px-3 py-2 ${typeof cell === "number" ? "text-right font-semibold" : ""}`}>
                      {cell ?? ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function Ask() {
  const ask = useAsk();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end", behavior: "smooth" }); // returns a Promise in some browsers, so no implicit return
  }, [turns, ask.isPending]);

  function send(question: string) {
    const q = question.trim();
    if (q.length < 3 || ask.isPending) return;
    setText("");
    setTurns((t) => [...t, { question: q }]);
    ask.mutate(q, {
      onSuccess: (reply) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, reply } : x))),
      onError: (e) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, failed: e.message } : x))),
    });
  }

  return (
    <>
      <h1 className="text-4xl font-extrabold">Ask</h1>
      <p className="mt-1 text-muted">Ask about stores, products or transfers in your own words.</p>

      {turns.length === 0 && (
        <div className="mt-6">
          <p className="font-bold">Try one of these</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <li key={s}>
                <button type="button" onClick={() => send(s)} className="min-h-11 rounded-2xl border border-line bg-paper px-4 py-2 text-left font-semibold hover:border-teal hover:bg-teal-tint">
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ol className="mt-6 grid gap-5" aria-label="Conversation">
        {turns.map((t, i) => (
          <li key={i} className="grid gap-3">
            <p className="ml-auto max-w-[85%] rounded-2xl rounded-tr-md bg-ink px-4 py-3 font-semibold text-white">{t.question}</p>
            {t.reply && <Answer r={t.reply} />}
            {t.failed && (
              <p role="alert" className="rounded-2xl bg-signal-tint p-4 font-semibold text-signal-deep">
                {t.failed}
              </p>
            )}
            {!t.reply && !t.failed && (
              <div role="status">
                {ask.error ? null : <p className="text-muted">Looking that up…</p>}
              </div>
            )}
          </li>
        ))}
      </ol>
      {ask.error && (ask.error as { code?: string }).code === "warming_up" && <div className="mt-4"><Warming /></div>}
      <div ref={end} />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(text);
        }}
        className="sticky bottom-[calc(4.75rem+env(safe-area-inset-bottom))] mt-6 flex gap-2 rounded-2xl bg-mist/90 py-2 backdrop-blur lg:bottom-4"
      >
        <label className="flex-1">
          <span className="sr-only">Your question</span>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={500}
            placeholder="Ask a question"
            className="min-h-14 w-full rounded-2xl border border-line bg-paper px-4 text-lg"
          />
        </label>
        <button
          type="submit"
          disabled={ask.isPending || text.trim().length < 3}
          className="grid min-h-14 min-w-14 place-items-center rounded-2xl bg-ink px-4 font-extrabold text-white disabled:bg-line disabled:text-muted"
        >
          <span className="sr-only">Ask</span>
          <SendHorizontal className="size-6" aria-hidden />
        </button>
      </form>
    </>
  );
}
