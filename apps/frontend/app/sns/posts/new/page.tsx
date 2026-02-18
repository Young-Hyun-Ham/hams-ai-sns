'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Bot, apiClient, authHeader } from '../../../../lib/api';
import { useAppStore } from '../../../../stores/app-store';

export default function SnsPostCreatePage() {
  const [category, setCategory] = useState<'경제' | '문화' | '연예' | '유머'>('경제');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [botId, setBotId] = useState<string>('');
  const [bots, setBots] = useState<Bot[]>([]);
  const [error, setError] = useState('');
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);
  const router = useRouter();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!token) return;
    apiClient
      .get<Bot[]>('/bots', { headers: authHeader(token) })
      .then((res) => setBots(res.data))
      .catch(() => setBots([]));
  }, [token]);

  const submit = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      await apiClient.post(
        '/sns/posts',
        {
          category,
          title,
          content,
          is_anonymous: isAnonymous,
          bot_id: botId ? Number(botId) : null
        },
        { headers: authHeader(token) }
      );
      router.push('/sns/posts');
    } catch {
      setError('게시글 등록에 실패했습니다.');
    }
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-2xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">SNS 게시글 등록</h1>
        <Link className="rounded-lg border border-border px-3 py-2" href="/sns/posts">목록</Link>
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="grid gap-3">
          <select className="rounded-lg border border-border bg-transparent p-2" value={category} onChange={(e) => setCategory(e.target.value as '경제' | '문화' | '연예' | '유머')}>
            <option value="경제">경제</option>
            <option value="문화">문화</option>
            <option value="연예">연예</option>
            <option value="유머">유머</option>
          </select>
          <input className="rounded-lg border border-border bg-transparent p-2" placeholder="제목" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea className="min-h-40 rounded-lg border border-border bg-transparent p-2" placeholder="내용" value={content} onChange={(e) => setContent(e.target.value)} />
          <select className="rounded-lg border border-border bg-transparent p-2" value={botId} onChange={(e) => setBotId(e.target.value)}>
            <option value="">수동 작성</option>
            {bots.map((bot) => (
              <option key={bot.id} value={bot.id}>{bot.name}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isAnonymous} onChange={(e) => setIsAnonymous(e.target.checked)} />
            익명 게시글로 등록
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={submit}>등록하기</button>
        </div>
      </section>
    </main>
  );
}
