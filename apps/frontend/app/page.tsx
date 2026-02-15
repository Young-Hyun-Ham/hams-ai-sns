'use client';

import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';

import { ThemeToggle } from '../components/theme-toggle';
import { useAppStore } from '../stores/app-store';

type LoginResponse = { access_token: string };
type Bot = {
  id: number;
  user_id: number;
  name: string;
  persona: string;
  topic: string;
  is_active: boolean;
};

type ActivityEvent = {
  type: string;
  data: { message?: string; executed_at?: string; user_id?: number };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function HomePage() {
  const [email, setEmail] = useState('owner@hams.local');
  const [password, setPassword] = useState('hams1234');
  const [status, setStatus] = useState('대기');
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [name, setName] = useState('');
  const [persona, setPersona] = useState('친근한 마케터');
  const [topic, setTopic] = useState('AI 자동화');

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

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : undefined;

  const login = async () => {
    const res = await axios.post<LoginResponse>(`${API_BASE}/auth/login`, { email, password });
    setAccessToken(res.data.access_token);
  };

  const loadBots = async () => {
    if (!authHeaders) return;
    const res = await axios.get<Bot[]>(`${API_BASE}/bots`, { headers: authHeaders });
    setBots(res.data);
  };

  const createBot = async () => {
    if (!authHeaders || !name) return;
    await axios.post(
      `${API_BASE}/bots`,
      { name, persona, topic },
      { headers: authHeaders }
    );
    setName('');
    await loadBots();
  };

  const toggleBot = async (bot: Bot) => {
    if (!authHeaders) return;
    await axios.patch(
      `${API_BASE}/bots/${bot.id}`,
      { is_active: !bot.is_active },
      { headers: authHeaders }
    );
    await loadBots();
  };

  const deleteBot = async (botId: number) => {
    if (!authHeaders) return;
    await axios.delete(`${API_BASE}/bots/${botId}`, { headers: authHeaders });
    await loadBots();
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
    <main className="mx-auto min-h-[100dvh] max-w-4xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">HAMS AI SNS Dashboard</h1>
        <ThemeToggle />
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-sm text-fg/80">로그인 후 봇 등록/수정/삭제와 실시간 알림을 사용할 수 있습니다.</p>
        <div className="grid gap-2">
          <input className="rounded-lg border border-border bg-transparent p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={login}>로그인</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={loadBots}>봇 목록 조회</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={connectWebSocket}>실시간 연결</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={clearAccessToken}>토큰 삭제</button>
          </div>
        </div>
        <p className="mt-2 break-all text-xs">token: {token || '없음'}</p>
        <p className="mt-1 text-sm">상태: {status}</p>
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-medium">봇 등록</h2>
        <div className="grid gap-2 md:grid-cols-3">
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="봇 이름" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="페르소나" value={persona} onChange={(e) => setPersona(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="토픽" value={topic} onChange={(e) => setTopic(e.target.value)} />
        </div>
        <button className="mt-2 rounded-lg bg-primary px-3 py-2 text-white" onClick={createBot}>봇 등록</button>
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-medium">봇 목록 (수정/삭제)</h2>
        <ul className="space-y-2 text-sm">
          {bots.map((bot) => (
            <li key={bot.id} className="rounded-md border border-border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium">{bot.name}</p>
                  <p className="text-xs text-fg/70">persona: {bot.persona} / topic: {bot.topic}</p>
                  <p className="text-xs">status: {bot.is_active ? 'active' : 'inactive'}</p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded border border-border px-2 py-1" onClick={() => toggleBot(bot)}>
                    {bot.is_active ? '비활성화' : '활성화'}
                  </button>
                  <button className="rounded border border-border px-2 py-1" onClick={() => deleteBot(bot.id)}>
                    삭제
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
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
