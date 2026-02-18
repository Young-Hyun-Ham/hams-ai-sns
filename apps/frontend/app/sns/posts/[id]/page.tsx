'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { Bot, CommentDepthSetting, SnsComment, SnsPost, apiClient, authHeader } from '../../../../lib/api';
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
  const [replyParentId, setReplyParentId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [maxCommentDepth, setMaxCommentDepth] = useState(3);

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

    apiClient.get<CommentDepthSetting>('/settings/comment-depth', headers)
      .then((res) => setMaxCommentDepth(res.data.max_comment_depth))
      .catch(() => setMaxCommentDepth(3));
  }, [params.id, token]);

  const addComment = async () => {
    if (!token || !newComment.trim()) return;

    try {
      await apiClient.post(
        `/sns/posts/${params.id}/comments`,
        {
          content: newComment.trim(),
          bot_id: commentBotId ? Number(commentBotId) : null,
          parent_comment_id: replyParentId,
        },
        { headers: authHeader(token) }
      );
      setNewComment('');
      setCommentBotId('');
      setReplyParentId(null);
      await loadComments();
    } catch {
      setError('댓글 등록에 실패했습니다.');
    }
  };

  const { roots, childrenMap, depthMap } = useMemo(() => {
    const rootsLocal: SnsComment[] = [];
    const childrenLocal = new Map<number, SnsComment[]>();
    const depthLocal = new Map<number, number>();

    comments.forEach((comment) => {
      if (!comment.parent_comment_id) {
        rootsLocal.push(comment);
        return;
      }
      const arr = childrenLocal.get(comment.parent_comment_id) ?? [];
      arr.push(comment);
      childrenLocal.set(comment.parent_comment_id, arr);
    });

    const assignDepth = (comment: SnsComment, depth: number) => {
      depthLocal.set(comment.id, depth);
      const children = childrenLocal.get(comment.id) ?? [];
      children.forEach((child) => assignDepth(child, depth + 1));
    };
    rootsLocal.forEach((root) => assignDepth(root, 1));

    return { roots: rootsLocal, childrenMap: childrenLocal, depthMap: depthLocal };
  }, [comments]);

  const renderCommentNode = (comment: SnsComment) => {
    const replies = childrenMap.get(comment.id) ?? [];
    const depth = depthMap.get(comment.id) ?? 1;
    const canReply = depth < maxCommentDepth;
    return (
      <li key={comment.id} className="rounded-lg border border-border p-3">
        <p className="text-sm break-words">{comment.content}</p>
        <p className="mt-1 text-xs text-fg/70">
          {comment.bot_name ? `${comment.bot_name} 봇` : '사용자'} · {new Date(comment.created_at).toLocaleString()}
        </p>
        {canReply ? (
          <button className="mt-1 text-xs text-primary underline" onClick={() => setReplyParentId(comment.id)}>답글</button>
        ) : (
          <p className="mt-1 text-xs text-fg/60">최대 depth({maxCommentDepth}) 도달</p>
        )}

        {replies.length > 0 && (
          <ul className="mt-2 space-y-2 border-l border-border pl-3">
            {replies.map((reply) => renderCommentNode(reply))}
          </ul>
        )}
      </li>
    );
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
        <h2 className="mb-1 font-medium">댓글</h2>
        <p className="mb-3 text-xs text-fg/70">현재 최대 답글 depth: {maxCommentDepth}</p>

        {replyParentId && (
          <p className="mb-2 text-xs text-primary">
            댓글 #{replyParentId}에 답글 작성 중
            <button className="ml-2 underline" onClick={() => setReplyParentId(null)}>취소</button>
          </p>
        )}

        <div className="mb-3 grid gap-2">
          <textarea
            className="min-h-24 rounded-lg border border-border bg-transparent p-2"
            placeholder={replyParentId ? '답글을 입력하세요' : '댓글을 입력하세요'}
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
            <button className="whitespace-nowrap rounded-lg bg-primary px-3 py-2 text-white" onClick={addComment}>{replyParentId ? '답글 등록' : '댓글 등록'}</button>
          </div>
        </div>

        <ul className="space-y-3">
          {roots.map((comment) => renderCommentNode(comment))}
        </ul>
      </section>
    </main>
  );
}
