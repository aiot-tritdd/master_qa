"use client";
import { useEffect, useState } from "react";
import { viewer, SystemDoc } from "@/lib/api";

export default function SystemPage() {
  const [docs, setDocs] = useState<SystemDoc[]>([]);
  useEffect(() => {
    viewer.systemdoc().then(setDocs).catch(() => setDocs([]));
  }, []);
  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-emerald-800">🗺 Tài liệu hệ thống (sống)</h1>
      <p className="text-emerald-700/70 mb-6">
        Mô tả code đang làm gì — không phải oracle. Lớn dần mỗi lần QA chạy.
      </p>
      {docs.length === 0 && (
        <p>Chưa có mục nào. Chạy /testcase-suggest để gieo hạt.</p>
      )}
      {docs.map((d) => (
        <div key={d.flow} className="card p-6 mb-4">
          <h2 className="font-semibold mb-1">{d.flow}</h2>
          <p className="text-xs text-stone-500 mb-3">
            nguồn: {JSON.stringify(d.meta.source_symbols)} · hash {String(d.meta.source_hash)}
          </p>
          <pre className="whitespace-pre-wrap text-sm bg-stone-50 rounded-2xl p-5 border border-stone-200">
            {d.body}
          </pre>
        </div>
      ))}
    </main>
  );
}
