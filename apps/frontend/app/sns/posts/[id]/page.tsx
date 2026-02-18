'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Bot, SnsComment, SnsPost, apiClient, authHeader } from '../../../../lib/api';
import { useAppStore } from '../../../../stores/app-store';

export default function SnsPostDetailPage() {
  const params = useParams<{ id: string }>();
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [post, setPost] = useState<SnsPost | null>(null);
  const [comments, setComments] = useState<SnsComment[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [commentBotId, setCommentBotId] = useState('');
  const [newComment, setNewComment] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadComments = async () => {
    if (!token || !params.id) return;
    try {
      const res = await apiClient.get<SnsComment[]>(`/sns/posts/${params.id}/comments`, { headers: authHeader(token) });
      setComments(res.data);
    } catch {
      setComments([]);
    }
  };

  useEffect(() => {
    if (!token || !params.id) return;

    const headers = { headers: authHeader(token) };
    apiClient.get<SnsPost>(`/sns/posts/${params.id}`, headers)
      .then((res) => setPost(res.data))
      .catch(() => setError('게시글 조회 실패'));

    loadComments();

    apiClient.get<Bot[]>('/bots', headers)
      .then((res) => setBots(res.data))
      .catch(() => setBots([]));
  }, [params.id, token]);

  const addComment = async () => {
    if (!token || !newComment.trim()) return;

    try {
      await apiClient.post(
        `/sns/posts/${params.id}/comments`,
        { content: newComment.trim(), bot_id: commentBotId ? Number(commentBotId) : null },
        { headers: authHeader(token) }
      );
      setNewComment('');
      setCommentBotId('');
      await loadComments();
    } catch {
      setError('댓글 등록에 실패했습니다.');
    }
  };

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
            [{post.category}] · {post.is_anonymous ? '익명' : '실명'} · {post.bot_name ? `${post.bot_name} 봇` : '수동 작성'} · {new Date(post.created_at).toLocaleString()}
          </p>
        </section>
      )}

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 font-medium">댓글</h2>

        <div className="mb-3 grid gap-2">
          <textarea
            className="min-h-24 rounded-lg border border-border bg-transparent p-2"
            placeholder="댓글을 입력하세요"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            <select
              className="min-w-40 rounded-lg border border-border bg-transparent p-2"
              value={commentBotId}
              onChange={(e) => setCommentBotId(e.target.value)}
            >
              <option value="">내 계정으로 작성</option>
              {bots.map((bot) => (
                <option key={bot.id} value={bot.id}>{bot.name} 봇으로 작성</option>
              ))}
            </select>
            <button className="whitespace-nowrap rounded-lg bg-primary px-3 py-2 text-white" onClick={addComment}>댓글 등록</button>
          </div>
        </div>

        <ul className="space-y-2">
          {comments.map((comment) => (
            <li key={comment.id} className="rounded-lg border border-border p-3">
              <p className="text-sm break-words">{comment.content}</p>
              <p className="mt-1 text-xs text-fg/70">
                {comment.bot_name ? `${comment.bot_name} 봇` : '사용자'} · {new Date(comment.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
