'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { SnsPost, apiClient, authHeader } from '../../../lib/api';
import { useAppStore } from '../../../stores/app-store';

type CategoryFilter = '전체' | '경제' | '문화' | '연예' | '유머';

export default function SnsPostListPage() {
  const [posts, setPosts] = useState<SnsPost[]>([]);
  const [error, setError] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('전체');
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadPosts = async () => {
    if (!token) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      const res = await apiClient.get<SnsPost[]>('/sns/posts', { headers: authHeader(token) });
      setPosts(res.data);
      setError('');
    } catch {
      setError('게시글 목록 조회에 실패했습니다.');
    }
  };

  useEffect(() => {
    if (token) {
      loadPosts();
    }
  }, [token]);

  const filteredPosts = useMemo(() => {
    if (categoryFilter === '전체') return posts;
    return posts.filter((post) => post.category === categoryFilter);
  }, [posts, categoryFilter]);

  return (
    <main className="mx-auto min-h-[100dvh] max-w-3xl bg-bg px-4 pb-[calc(env(safe-area-inset-bottom)+24px)] pt-[calc(env(safe-area-inset-top)+24px)]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">SNS 게시글 목록</h1>
        <div className="flex gap-2">
          <Link className="rounded-lg border border-border px-3 py-2" href="/">홈</Link>
          <Link className="rounded-lg bg-primary px-3 py-2 text-white" href="/sns/posts/new">등록</Link>
        </div>
      </header>

      <div className="mb-3 flex items-center justify-between gap-2">
        <select
          className="rounded-lg border border-border bg-transparent px-3 py-2"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
        >
          <option value="전체">전체 카테고리</option>
          <option value="경제">경제</option>
          <option value="문화">문화</option>
          <option value="연예">연예</option>
          <option value="유머">유머</option>
        </select>
        <button className="rounded-lg border border-border px-3 py-2" onClick={loadPosts}>새로고침</button>
      </div>
      {error && <p className="mb-3 text-sm text-red-500">{error}</p>}

      <ul className="space-y-3">
        {filteredPosts.map((post) => (
          <li key={post.id} className="rounded-xl border border-border bg-card p-4">
            <div className="mb-1 flex items-center justify-between gap-3">
              <Link className="font-medium text-primary underline" href={`/sns/posts/${post.id}`}>{post.title}</Link>
              {post.can_edit && (
                <Link className="text-sm text-primary underline" href={`/sns/posts/${post.id}/edit`}>수정/삭제</Link>
              )}
            </div>
            <p className="text-sm text-fg/90">{post.content}</p>
            <p className="mt-2 text-xs text-fg/70">
              [{post.category}] · {post.is_anonymous ? '익명' : '실명'} · {post.bot_name ? `${post.bot_name} 봇` : '수동 작성'} · 댓글 {post.comment_count}개 · {new Date(post.created_at).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>
    </main>
  );
}
