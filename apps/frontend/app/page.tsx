'use client';

import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';

import { ThemeToggle } from '../components/theme-toggle';
import { useAppStore } from '../stores/app-store';

type LoginResponse = {
  access_token: string;
};

type ActivityEvent = {
  type: string;
  data: {
    message?: string;
    executed_at?: string;
    user_id?: number;
  };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function HomePage() {
  const [email, setEmail] = useState('owner@hams.local');
  const [password, setPassword] = useState('hams1234');
  const [status, setStatus] = useState('대기');
  const [events, setEvents] = useState<ActivityEvent[]>([]);

  const token = useAppStore((s) => s.accessToken);
  const setAccessToken = useAppStore((s) => s.setAccessToken);
  const clearAccessToken = useAppStore((s) => s.clearAccessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const wsUrl = useMemo(() => {
    const base = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');
    return `${base}/ws/activity?token=${encodeURIComponent(token)}`;
  }, [token]);

  const login = async () => {
    const res = await axios.post<LoginResponse>(`${API_BASE}/auth/login`, { email, password });
    setAccessToken(res.data.access_token);
  };

  const connectWebSocket = () => {
    if (!token) {
      alert('먼저 로그인하세요.');
      return;
    }

    const ws = new WebSocket(wsUrl);
    setStatus('연결 중...');

    ws.onopen = () => setStatus('연결됨');
    ws.onclose = () => setStatus('종료됨');
    ws.onerror = () => setStatus('에러');
    ws.onmessage = (evt) => {
      const parsed: ActivityEvent = JSON.parse(evt.data);
      setEvents((prev) => [parsed, ...prev].slice(0, 30));
    };
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-3xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">HAMS AI SNS - Step 8 Capacitor Ready</h1>
        <ThemeToggle />
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-sm text-fg/80">Storage Adapter 기반으로 토큰/테마를 유지합니다.</p>
        <div className="grid gap-2">
          <input className="rounded-lg border border-border bg-transparent p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={login}>로그인</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={connectWebSocket}>실시간 연결</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={clearAccessToken}>토큰 삭제</button>
          </div>
        </div>
        <p className="mt-2 break-all text-xs">token: {token || '없음'}</p>
        <p className="mt-1 text-sm">상태: {status}</p>
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-medium">실시간 이벤트</h2>
        <ul className="space-y-2 text-sm">
          {events.map((evt, idx) => (
            <li key={`${evt.type}-${idx}`} className="rounded-md border border-border p-2">
              [{evt.type}] {evt.data.executed_at ?? ''} {evt.data.message ?? `user_id=${evt.data.user_id}`}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
