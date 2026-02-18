'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { Bot, SnsComment, SnsPost, apiClient, authHeader } from '../../../../../lib/api';
import { useAppStore } from '../../../../../stores/app-store';

export default function SnsPostEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [category, setCategory] = useState<'경제' | '문화' | '연예' | '유머'>('경제');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [botId, setBotId] = useState<string>('');
  const [bots, setBots] = useState<Bot[]>([]);
  const [comments, setComments] = useState<SnsComment[]>([]);
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingCommentText, setEditingCommentText] = useState('');
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
    apiClient.get<SnsPost>(`/sns/posts/${params.id}`, headers).then((res) => {
      if (!res.data.can_edit) {
        router.replace(`/sns/posts/${params.id}`);
        return;
      }
      setCategory(res.data.category);
      setTitle(res.data.title);
      setContent(res.data.content);
      setIsAnonymous(res.data.is_anonymous);
      setBotId(res.data.bot_id ? String(res.data.bot_id) : '');
    }).catch(() => setError('게시글 조회에 실패했습니다.'));

    apiClient.get<Bot[]>('/bots', headers).then((res) => setBots(res.data)).catch(() => setBots([]));
    loadComments();
  }, [params.id, token]);

  const update = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      await apiClient.patch(
        `/sns/posts/${params.id}`,
        { category, title, content, is_anonymous: isAnonymous, bot_id: botId ? Number(botId) : null },
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

  const startEditComment = (comment: SnsComment) => {
    if (!comment.can_edit) return;
    setEditingCommentId(comment.id);
    setEditingCommentText(comment.content);
  };

  const saveComment = async () => {
    if (!token || !editingCommentId || !editingCommentText.trim()) return;

    try {
      await apiClient.patch(
        `/sns/comments/${editingCommentId}`,
        { content: editingCommentText.trim() },
        { headers: authHeader(token) }
      );
      setEditingCommentId(null);
      setEditingCommentText('');
      loadComments();
    } catch {
      setError('댓글 수정에 실패했습니다.');
    }
  };

  const removeComment = async (commentId: number) => {
    if (!token) return;

    try {
      await apiClient.delete(`/sns/comments/${commentId}`, { headers: authHeader(token) });
      loadComments();
    } catch {
      setError('댓글 삭제에 실패했습니다.');
    }
  };

  const { roots, childrenMap } = useMemo(() => {
    const rootsLocal: SnsComment[] = [];
    const childrenLocal = new Map<number, SnsComment[]>();

    comments.forEach((comment) => {
      if (!comment.parent_comment_id) {
        rootsLocal.push(comment);
        return;
      }
      const arr = childrenLocal.get(comment.parent_comment_id) ?? [];
      arr.push(comment);
      childrenLocal.set(comment.parent_comment_id, arr);
    });

    return { roots: rootsLocal, childrenMap: childrenLocal };
  }, [comments]);

  const renderEditableComment = (comment: SnsComment) => {
    const replies = childrenMap.get(comment.id) ?? [];

    return (
      <li key={comment.id} className="rounded-lg border border-border p-3">
        {editingCommentId === comment.id ? (
          <div className="space-y-2">
            <p className="text-xs text-fg/70">
              [게시글 #{comment.post_id}] {comment.parent_comment_id ? `댓글 #${comment.parent_comment_id}의 답글` : '최상위 댓글'}
            </p>
            <textarea
              className="w-full rounded-lg border border-border bg-transparent p-2"
              value={editingCommentText}
              onChange={(e) => setEditingCommentText(e.target.value)}
            />
            <div className="flex gap-2">
              <button className="whitespace-nowrap rounded border border-border px-2 py-1" onClick={saveComment}>저장</button>
              <button className="whitespace-nowrap rounded border border-border px-2 py-1" onClick={() => setEditingCommentId(null)}>취소</button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-xs text-fg/70">
                [게시글 #{comment.post_id}] {comment.parent_comment_id ? `댓글 #${comment.parent_comment_id}의 답글` : '최상위 댓글'}
              </p>
              <p className="text-sm break-words">{comment.content}</p>
              <p className="text-xs text-fg/70">
                {comment.bot_name ? `${comment.bot_name} 봇` : '사용자'} · {new Date(comment.created_at).toLocaleString()}
              </p>
            </div>
            {comment.can_edit && (
              <div className="flex shrink-0 gap-2 text-xs whitespace-nowrap">
                <button className="whitespace-nowrap rounded border border-border px-2 py-1" onClick={() => startEditComment(comment)}>수정</button>
                <button className="whitespace-nowrap rounded border border-red-300 px-2 py-1 text-red-500" onClick={() => removeComment(comment.id)}>삭제</button>
              </div>
            )}
          </div>
        )}

        {replies.length > 0 && (
          <ul className="mt-2 space-y-2 border-l border-border pl-3">
            {replies.map((reply) => renderEditableComment(reply))}
          </ul>
        )}
      </li>
    );
  };

  return (
    <main className="mx-auto min-h-[100dvh] max-w-2xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">SNS 게시글 수정</h1>
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
            익명 게시글
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2">
            <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={update}>수정 저장</button>
            <button className="rounded-lg border border-red-400 px-3 py-2 text-red-500" onClick={remove}>삭제</button>
          </div>
        </div>
      </section>

      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 font-medium">댓글</h2>

        <p className="mb-3 text-xs text-fg/70">수정 화면에서는 댓글 신규 작성이 비활성화됩니다. 댓글 등록은 상세 화면에서 가능합니다.</p>

        <ul className="space-y-2">
          {roots.map((comment) => renderEditableComment(comment))}
        </ul>
      </section>
    </main>
  );
}
