'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { SnsComment, SnsPost, apiClient, authHeader } from '../../../../lib/api';
import { useAppStore } from '../../../../stores/app-store';

export default function SnsPostDetailPage() {
  const params = useParams<{ id: string }>();
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [post, setPost] = useState<SnsPost | null>(null);
  const [comments, setComments] = useState<SnsComment[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!token || !params.id) return;

    const headers = { headers: authHeader(token) };
    apiClient.get<SnsPost>(`/sns/posts/${params.id}`, headers)
      .then((res) => setPost(res.data))
      .catch(() => setError('게시글 조회 실패'));

    apiClient.get<SnsComment[]>(`/sns/posts/${params.id}/comments`, headers)
      .then((res) => setComments(res.data))
      .catch(() => setComments([]));
  }, [params.id, token]);

  return (
    <main className="mx-auto min-h-[100dvh] max-w-2xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">게시글 상세</h1>
        <div className="flex gap-2">
          <Link className="rounded-lg border border-border px-3 py-2" href="/sns/posts">목록</Link>
          {post?.can_edit && <Link className="rounded-lg border border-border px-3 py-2" href={`/sns/posts/${params.id}/edit`}>수정</Link>}
        </div>
      </header>

      {error && <p className="mb-3 text-sm text-red-500">{error}</p>}

      {post && (
        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 text-lg font-medium">{post.title}</h2>
          <p className="whitespace-pre-wrap text-sm text-fg/90">{post.content}</p>
          <p className="mt-2 text-xs text-fg/70">
            {post.is_anonymous ? '익명' : '실명'} · {post.bot_name ? `${post.bot_name} 봇` : '수동 작성'} · {new Date(post.created_at).toLocaleString()}
          </p>
        </section>
      )}

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 font-medium">댓글</h2>
        <ul className="space-y-2">
          {comments.map((comment) => (
            <li key={comment.id} className="rounded-lg border border-border p-3">
              <p className="text-sm">{comment.content}</p>
              <p className="text-xs text-fg/70">{new Date(comment.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
