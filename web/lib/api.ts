const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8899";

export type Status = {
  doc: { status: string; spans_repos: string[] } | null;
  tests_exist: boolean;
  last_run: { passed: boolean; output: string } | null;
};
export type Doc = { meta: Record<string, any>; body: string };

const j = (r: Response) => {
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
};

export const api = {
  status: (): Promise<Status> =>
    fetch(`${BASE}/api/status`, { cache: "no-store" }).then(j),
  doc: (): Promise<Doc> => fetch(`${BASE}/api/doc`, { cache: "no-store" }).then(j),
  extract: () => fetch(`${BASE}/api/extract`, { method: "POST" }).then(j),
  approve: () => fetch(`${BASE}/api/approve`, { method: "POST" }).then(j),
  generate: () => fetch(`${BASE}/api/generate`, { method: "POST" }).then(j),
  run: (): Promise<{ passed: boolean; output: string }> =>
    fetch(`${BASE}/api/run`, { method: "POST" }).then(j),
};

export type SystemDoc = { flow: string; meta: Record<string, any>; body: string };
export const viewer = {
  systemdoc: (): Promise<SystemDoc[]> =>
    fetch(`${BASE}/api/systemdoc`, { cache: "no-store" }).then(j),
  folder: (path: string) =>
    fetch(`${BASE}/api/folder?path=${encodeURIComponent(path)}`, { cache: "no-store" }).then(j),
};
