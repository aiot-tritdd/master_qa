"use client";
import { useState } from "react";
import { viewer } from "@/lib/api";

export default function FolderPage() {
  const [path, setPath] = useState("");
  const [data, setData] = useState<any>(null);
  const load = () => viewer.folder(path).then(setData).catch(() => setData(null));
  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-emerald-800">📋 Test folder</h1>
      <div className="flex gap-2 my-4">
        <input
          className="border rounded-full px-4 py-2 flex-1"
          placeholder="đường dẫn folder"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
        <button className="btn bg-emerald-300" onClick={load}>
          Tải
        </button>
      </div>
      {data?.tcs?.tcs?.map((t: any) => (
        <div key={t.id} className="card p-4 mb-2">
          <b>{t.id}</b> · {t.title} —{" "}
          <span className="font-mono text-sm">{t.result}</span>
          <p className="text-sm text-stone-600 mt-1">expect: {t.expect}</p>
          <p className="text-xs text-stone-500">{t.note}</p>
        </div>
      ))}
    </main>
  );
}
