import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, type Me, type Overview, type Run, type Settings } from "./api";

import { replayRun, type Replay, type DemoCase } from "./replay";

interface Ctx {
  startReplay: (issue: DemoCase) => void;
  runs: Run[];
  overview: Overview | null;
  settings: Settings | null;
  me: Me | null;
  authState: "loading" | "signedout" | "ready";
  signOut: () => Promise<void>;
  error: string | null;
  loaded: boolean;
  repoFilter: string;
  setRepoFilter: (r: string) => void;
  selectedId: string | null;
  select: (id: string | null) => void;
  selected: Run | null; // list-level run
  detail: Run | null; // full run (logs, diff…)
  refresh: () => Promise<void>;
  reloadSettings: () => Promise<void>;
  toast: string;
  notify: (t: string) => void;
}

const DataCtx = createContext<Ctx>(null as unknown as Ctx);
export const useData = () => useContext(DataCtx);

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [authState, setAuthState] = useState<"loading" | "signedout" | "ready">("loading");
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [repoFilter, setRepoFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Run | null>(null);
  const [toast, setToast] = useState("");
  const toastTimer = useRef<number | undefined>(undefined);
  const selRef = useRef<string | null>(null);
  selRef.current = selectedId;

  const notify = useCallback((t: string) => {
    setToast(t);
    window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(""), 4500);
  }, []);

  const storageKey = "arcane.replays." + (me?.login ?? "local");
  const [entries, setEntries] = useState<Replay[]>([]);
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    try { setEntries(JSON.parse(sessionStorage.getItem(storageKey) ?? "[]")); }
    catch { setEntries([]); }
    setNow(Date.now());
  }, [storageKey]);
  const active = entries.some(e => now < e.start + 30000);
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setNow(Date.now()), 400);
    return () => window.clearInterval(timer);
  }, [active]);
  const startReplay = (issue: DemoCase) => {
    const start = Date.now();
    const id = "replay-" + crypto.randomUUID().slice(0, 8);
    const next = [{ id, start, issue }, ...entries].slice(0, 30);
    setEntries(next);
    try { sessionStorage.setItem(storageKey, JSON.stringify(next)); } catch { /* In-memory playback still works. */ }
    setNow(start);
    setSelectedId(id);
    selRef.current = id;
    setRepoFilter("");
  };

  const refresh = useCallback(async () => {
    if (authRef.current !== "ready") return;
    try {
      const [o, r] = await Promise.all([api.overview(), api.runs("?limit=200")]);
      setOverview(o);
      setRuns(r.runs);
      setError(null);
      const id = selRef.current ?? r.runs[0]?.id ?? null;
      if (id && !id.startsWith("replay-")) {
        if (!selRef.current) setSelectedId(id);
        try {
          setDetail(await api.run(id));
        } catch {
          // The selected run no longer exists (e.g. store was reset) — fall back to the newest one.
          setDetail(null);
          if (!r.runs.some((x) => x.id === id)) setSelectedId(r.runs[0]?.id ?? null);
        }
      } else {
        setDetail(null);
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setAuthState("signedout");
        return;
      }
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setLoaded(true);
    }
  }, []);

  const reloadSettings = useCallback(async () => {
    try {
      setSettings(await api.settings());
    } catch {
      /* surfaced through the main error banner */
    }
  }, []);

  const authRef = useRef(authState);
  authRef.current = authState;

  useEffect(() => {
    api
      .me()
      .then((m) => {
        setMe(m);
        authRef.current = "ready";
        setAuthState("ready");
        reloadSettings();
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) setAuthState("signedout");
        else {
          setError(e instanceof ApiError ? e.message : String(e));
          setAuthState("ready");
        }
      });
  }, [reloadSettings]);

  const signOut = useCallback(async () => {
    await api.logout().catch(() => {});
    setMe(null);
    setRuns([]);
    setSettings(null);
    setAuthState("signedout");
  }, []);

  const anyWorking = runs.some((r) => r.status === "working");
  useEffect(() => {
    if (authState !== "ready") return;
    refresh();
    const t = window.setInterval(refresh, anyWorking ? 1500 : 4000);
    return () => window.clearInterval(t);
  }, [refresh, anyWorking, authState]);

  const select = useCallback(
    (id: string | null) => {
      setSelectedId(id);
      selRef.current = id;
      if (id && !id.startsWith("replay-")) api.run(id).then(setDetail).catch(() => {});
    },
    [],
  );

  const combined = useMemo(() => [...entries.map(e => replayRun(e, now)), ...runs], [entries, now, runs]);
  const selected = useMemo(() => combined.find((r) => r.id === selectedId) ?? null, [combined, selectedId]);

  const value: Ctx = {
    runs: combined, startReplay, overview, settings, me, authState, signOut, error, loaded, repoFilter, setRepoFilter,
    selectedId, select, selected, detail: selected?.source === "demo-replay" ? selected : detail && detail.id === selectedId ? detail : null,
    refresh, reloadSettings, toast, notify,
  };
  return <DataCtx.Provider value={value}>{children}</DataCtx.Provider>;
}
