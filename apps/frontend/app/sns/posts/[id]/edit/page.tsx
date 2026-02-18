'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Bot, SnsPost, apiClient, authHeader } from '../../../../../lib/api';
import { useAppStore } from '../../../../../stores/app-store';

export default function SnsPostEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [botId, setBotId] = useState<string>('');
  const [bots, setBots] = useState<Bot[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!token || !params.id) return;

    const headers = { headers: authHeader(token) };
    apiClient.get<SnsPost>(`/sns/posts/${params.id}`, headers).then((res) => {
      setTitle(res.data.title);
      setContent(res.data.content);
      setIsAnonymous(res.data.is_anonymous);
      setBotId(res.data.bot_id ? String(res.data.bot_id) : '');
    }).catch(() => setError('게시글 조회에 실패했습니다.'));

    apiClient.get<Bot[]>('/bots', headers).then((res) => setBots(res.data)).catch(() => setBots([]));
  }, [params.id, token]);

  const update = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      await apiClient.patch(
        `/sns/posts/${params.id}`,
        { title, content, is_anonymous: isAnonymous, bot_id: botId ? Number(botId) : null },
        { headers: authHeader(token) }
      );
      router.push('/sns/posts');
    } catch {
      setError('게시글 수정에 실패했습니다.');
    }
  };

  const remove = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      await apiClient.delete(`/sns/posts/${params.id}`, { headers: authHeader(token) });
      router.push('/sns/posts');
    } catch {
      setError('게시글 삭제에 실패했습니다.');
    }
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-2xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">SNS 게시글 수정</h1>
        <Link className="rounded-lg border border-border px-3 py-2" href="/sns/posts">목록</Link>
      </header>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="grid gap-3">
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
            익명 게시글
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2">
            <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={update}>수정 저장</button>
            <button className="rounded-lg border border-red-400 px-3 py-2 text-red-500" onClick={remove}>삭제</button>
          </div>
        </div>
      </section>
    </main>
  );
}
