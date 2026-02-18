'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Bot, apiClient, authHeader } from '../../../lib/api';
import { useAppStore } from '../../../stores/app-store';

export default function BotSettingsPage() {
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [bots, setBots] = useState<Bot[]>([]);
  const [name, setName] = useState('');
  const [persona, setPersona] = useState('친근한 PM');
  const [topic, setTopic] = useState('AI 자동화');
  const [error, setError] = useState('');

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadBots = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      const res = await apiClient.get<Bot[]>('/bots', { headers: authHeader(token) });
      setBots(res.data);
      setError('');
    } catch {
      setError('봇 목록 조회 실패');
    }
  };

  useEffect(() => {
    if (token) {
      loadBots();
    }
  }, [token]);

  const createBot = async () => {
    if (!token || !name.trim()) return;
    try {
      await apiClient.post('/bots', { name, persona, topic }, { headers: authHeader(token) });
      setName('');
      loadBots();
    } catch {
      setError('봇 등록 실패');
    }
  };

  const toggleBot = async (bot: Bot) => {
    if (!token) return;
    await apiClient.patch(`/bots/${bot.id}`, { is_active: !bot.is_active }, { headers: authHeader(token) });
    loadBots();
  };

  const deleteBot = async (botId: number) => {
    if (!token) return;
    await apiClient.delete(`/bots/${botId}`, { headers: authHeader(token) });
    loadBots();
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-3xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">AI 봇 설정</h1>
        <Link href="/" className="rounded-lg border border-border px-3 py-2">홈</Link>
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-medium">봇 등록</h2>
        <div className="grid gap-2 md:grid-cols-3">
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="봇 이름" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="페르소나" value={persona} onChange={(e) => setPersona(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="토픽" value={topic} onChange={(e) => setTopic(e.target.value)} />
        </div>
        <button className="mt-2 rounded-lg bg-primary px-3 py-2 text-white" onClick={createBot}>봇 등록</button>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="font-medium">봇 목록</h2>
          <button className="rounded border border-border px-2 py-1 text-sm" onClick={loadBots}>새로고침</button>
        </div>
        <ul className="space-y-2">
          {bots.map((bot) => (
            <li key={bot.id} className="rounded-lg border border-border p-3">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium">{bot.name}</p>
                  <p className="text-xs text-fg/70">{bot.persona} · {bot.topic}</p>
                  <p className="text-xs">상태: {bot.is_active ? '활성' : '비활성'}</p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded border border-border px-2 py-1" onClick={() => toggleBot(bot)}>{bot.is_active ? '중지' : '재개'}</button>
                  <button className="rounded border border-red-300 px-2 py-1 text-red-500" onClick={() => deleteBot(bot.id)}>삭제</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
