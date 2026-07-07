"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Status } from "@/lib/api";

export default function Home() {
  const [s, setS] = useState<Status | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const refresh = () => api.status().then(setS).catch(() => {});
  useEffect(() => {
    refresh();
  }, []);
  const act = async (name: string, fn: () => Promise<any>) => {
    setBusy(name);
    try {
      await fn();
    } finally {
      setBusy(null);
      refresh();
    }
  };
  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-4xl font-bold text-emerald-800">🌿 QA-Server</h1>
      <p className="text-emerald-700/70 mb-8">
        Con QA hiểu nghiệp vụ · flow: customer-sync (backend-ticket)
      </p>
      <div className="card p-6 mb-6">
        <h2 className="font-semibold mb-3">📚 Living doc</h2>
        <p className="mb-4">
          Trạng thái:{" "}
          <span
            className={`btn ${
              s?.doc?.status === "approved" ? "bg-emerald-200" : "bg-amber-200"
            }`}
          >
            {s?.doc?.status ?? "chưa có"}
          </span>
        </p>
        <div className="flex gap-3 flex-wrap">
          <button
            className="btn bg-sky-200"
            disabled={!!busy}
            onClick={() => act("extract", api.extract)}
          >
            {busy === "extract" ? "…" : "① Sinh doc nháp"}
          </button>
          <Link href="/doc" className="btn bg-stone-200">
            Xem / Duyệt doc
          </Link>
          <button
            className="btn bg-violet-200"
            disabled={!!busy}
            onClick={() => act("generate", api.generate)}
          >
            {busy === "generate" ? "…" : "③ Sinh test"}
          </button>
          <button
            className="btn bg-emerald-300"
            disabled={!!busy}
            onClick={() => act("run", api.run)}
          >
            {busy === "run" ? "đang chạy…" : "④ Chạy test"}
          </button>
        </div>
      </div>
      {s?.last_run && (
        <div className="card p-6">
          <h2 className="font-semibold mb-2">
            {s.last_run.passed ? "✅ PASS" : "❌ FAIL"}
          </h2>
          <pre className="text-xs whitespace-pre-wrap bg-stone-100 rounded-2xl p-4 max-h-96 overflow-auto">
            {s.last_run.output}
          </pre>
        </div>
      )}
    </main>
  );
}
