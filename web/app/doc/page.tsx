"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Doc } from "@/lib/api";

export default function DocPage() {
  const [doc, setDoc] = useState<Doc | null>(null);
  const [busy, setBusy] = useState(false);
  const refresh = () => api.doc().then(setDoc).catch(() => setDoc(null));
  useEffect(() => {
    refresh();
  }, []);
  const approve = async () => {
    setBusy(true);
    try {
      await api.approve();
    } finally {
      setBusy(false);
      refresh();
    }
  };
  if (!doc)
    return (
      <main className="max-w-3xl mx-auto p-8">
        Chưa có doc — bấm ① Sinh doc nháp trước.{" "}
        <Link className="underline" href="/">
          ← Dashboard
        </Link>
      </main>
    );
  const approved = doc.meta.status === "approved";
  return (
    <main className="max-w-3xl mx-auto p-8">
      <div className="card p-6">
        <p className="text-sm mb-3">
          status: <b>{doc.meta.status}</b> · repos:{" "}
          {JSON.stringify(doc.meta.spans_repos)}
        </p>
        <pre className="whitespace-pre-wrap text-sm bg-stone-50 rounded-2xl p-5 border border-stone-200">
          {doc.body}
        </pre>
        {approved ? (
          <p className="mt-4 text-emerald-700">Đã duyệt ✅</p>
        ) : (
          <button
            className="btn bg-emerald-300 mt-4"
            disabled={busy}
            onClick={approve}
          >
            {busy ? "…" : "✅ Duyệt (Approve) — chốt ý định"}
          </button>
        )}
        <div className="mt-4">
          <Link href="/" className="btn bg-stone-200">
            ← Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
