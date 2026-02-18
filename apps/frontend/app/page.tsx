'use client';

import SettingsIcon from '@mui/icons-material/Settings';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ThemeToggle } from '../components/theme-toggle';
import { apiClient } from '../lib/api';
import { useAppStore } from '../stores/app-store';

type LoginResponse = { access_token: string };

export default function HomePage() {
  const [email, setEmail] = useState('owner@hams.local');
  const [password, setPassword] = useState('hams1234');
  const [message, setMessage] = useState('');

  const token = useAppStore((s) => s.accessToken);
  const setAccessToken = useAppStore((s) => s.setAccessToken);
  const clearAccessToken = useAppStore((s) => s.clearAccessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const login = async () => {
    try {
      const res = await apiClient.post<LoginResponse>('/auth/login', { email, password });
      setAccessToken(res.data.access_token);
      setMessage('로그인 성공');
    } catch {
      setMessage('로그인 실패: 계정을 확인해주세요.');
    }
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-2xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Blind 스타일 SNS MVP</h1>
        <div className="flex items-center gap-2">
          <Link href="/settings/bots" className="rounded-lg border border-border p-2" aria-label="AI 봇 설정">
            <SettingsIcon fontSize="small" />
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 font-medium">로그인</h2>
        <div className="grid gap-2">
          <input className="rounded-lg border border-border bg-transparent p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="rounded-lg border border-border bg-transparent p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={login}>로그인</button>
            <button className="rounded-lg border border-border px-3 py-2" onClick={clearAccessToken}>로그아웃</button>
          </div>
        </div>
        <p className="mt-2 text-sm text-fg/80">{message || (token ? '인증 토큰이 저장되어 있습니다.' : '로그인 후 SNS 화면으로 이동하세요.')}</p>
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 font-medium">SNS 메뉴</h2>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-lg border border-border px-3 py-2" href="/sns/posts">게시글 목록</Link>
          <Link className="rounded-lg border border-border px-3 py-2" href="/sns/posts/new">게시글 등록</Link>
        </div>
      </section>
    </main>
  );
}
