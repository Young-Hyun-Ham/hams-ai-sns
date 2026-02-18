'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { AIModelListResponse, Bot, CommentDepthSetting, apiClient, authHeader } from '../../../lib/api';
import { useAppStore } from '../../../stores/app-store';

type AIProvider = 'mock' | 'gpt' | 'gemini' | 'claude';

export default function BotSettingsPage() {
  const token = useAppStore((s) => s.accessToken);
  const hydrate = useAppStore((s) => s.hydrate);

  const [bots, setBots] = useState<Bot[]>([]);
  const [name, setName] = useState('');
  const [persona, setPersona] = useState('친근한 PM');
  const [topic, setTopic] = useState('AI 자동화');
  const [aiProvider, setAiProvider] = useState<AIProvider>('gpt');
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState<string[]>([]);
  const [aiModel, setAiModel] = useState('');
  const [modelLoading, setModelLoading] = useState(false);
  const [error, setError] = useState('');
  const [maxCommentDepth, setMaxCommentDepth] = useState(3);
  const resolveToken = () => {
    if (token) return token;
    if (typeof window !== 'undefined') {
      return window.localStorage.getItem('hams_access_token') ?? '';
    }
    return '';
  };


  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadBots = async () => {
    const accessToken = resolveToken();
    if (!accessToken) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      const res = await apiClient.get<Bot[]>('/bots', { headers: authHeader(accessToken) });
      setBots(res.data);
      const depthRes = await apiClient.get<CommentDepthSetting>('/settings/comment-depth', { headers: authHeader(accessToken) });
      setMaxCommentDepth(depthRes.data.max_comment_depth);
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

  const fetchModels = async () => {
    const accessToken = resolveToken();
    if (!accessToken) {
      setError('로그인이 필요합니다.');
      return;
    }
    if (!apiKey.trim()) {
      setError('API Key를 먼저 입력해주세요.');
      return;
    }

    setModelLoading(true);
    try {
      const res = await apiClient.post<AIModelListResponse>(
        '/ai/models',
        { ai_provider: aiProvider, api_key: apiKey.trim() },
        { headers: authHeader(accessToken) }
      );
      setModels(res.data.models);
      setAiModel(res.data.models[0] ?? '');
      setError('');
    } catch (err: any) {
      setModels([]);
      setAiModel('');
      const message = err?.response?.data?.detail ?? '모델 조회 실패';
      setError(String(message));
    } finally {
      setModelLoading(false);
    }
  };

  const createBot = async () => {
    const accessToken = resolveToken();
    if (!accessToken || !name.trim()) return;
    if (!apiKey.trim()) {
      setError('API Key를 입력해주세요.');
      return;
    }
    if (!aiModel) {
      setError('모델 조회 후 모델을 선택해주세요.');
      return;
    }

    try {
      await apiClient.post(
        '/bots',
        {
          name,
          persona,
          topic,
          ai_provider: aiProvider,
          api_key: apiKey.trim(),
          ai_model: aiModel,
        },
        { headers: authHeader(accessToken) }
      );
      setName('');
      setApiKey('');
      setModels([]);
      setAiModel('');
      loadBots();
    } catch {
      setError('봇 등록 실패');
    }
  };

  const toggleBot = async (bot: Bot) => {
    const accessToken = resolveToken();
    if (!accessToken) return;
    await apiClient.patch(`/bots/${bot.id}`, { is_active: !bot.is_active }, { headers: authHeader(accessToken) });
    loadBots();
  };


  const saveDepthSetting = async () => {
    const accessToken = resolveToken();
    if (!accessToken) return;

    try {
      const depth = Math.max(1, Math.min(10, Number(maxCommentDepth) || 1));
      const res = await apiClient.patch<CommentDepthSetting>(
        '/settings/comment-depth',
        { max_comment_depth: depth },
        { headers: authHeader(accessToken) }
      );
      setMaxCommentDepth(res.data.max_comment_depth);
      setError('');
    } catch (err: any) {
      const message = err?.response?.data?.detail ?? '댓글 depth 설정 저장 실패';
      setError(String(message));
    }
  };

  const deleteBot = async (botId: number) => {
    const accessToken = resolveToken();
    if (!accessToken) return;
    await apiClient.delete(`/bots/${botId}`, { headers: authHeader(accessToken) });
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

        <div className="mt-2 grid gap-2 md:grid-cols-3">
          <select className="rounded-lg border border-border bg-transparent p-2" value={aiProvider} onChange={(e) => setAiProvider(e.target.value as AIProvider)}>
            <option value="gpt">gpt</option>
            <option value="gemini">gemini</option>
            <option value="claude">claude</option>
            <option value="mock">mock</option>
          </select>
          <input
            className="rounded-lg border border-border bg-transparent p-2"
            placeholder="API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button className="rounded-lg border border-border px-3 py-2" onClick={fetchModels} disabled={modelLoading}>
            {modelLoading ? '조회 중...' : '모델 조회'}
          </button>
        </div>

        <div className="mt-2 grid gap-2 md:grid-cols-2">
          <select
            className="rounded-lg border border-border bg-transparent p-2"
            value={aiModel}
            onChange={(e) => setAiModel(e.target.value)}
          >
            <option value="">모델 선택</option>
            {models.map((model) => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
          <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={createBot}>봇 등록</button>
        </div>

        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </section>


      <section className="mt-4 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-medium">댓글 Depth 설정</h2>
        <p className="mb-2 text-xs text-fg/70">사용자/AI 모두 이 최대 depth를 넘는 답글 작성이 차단됩니다. (1~10)</p>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="number"
            min={1}
            max={10}
            className="w-28 rounded-lg border border-border bg-transparent p-2"
            value={maxCommentDepth}
            onChange={(e) => setMaxCommentDepth(Number(e.target.value))}
          />
          <button className="rounded-lg bg-primary px-3 py-2 text-white" onClick={saveDepthSetting}>저장</button>
          <button className="rounded-lg border border-border px-3 py-2" onClick={loadBots}>새로고침</button>
        </div>
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
                  <p className="text-xs text-fg/70">AI: {bot.ai_provider} · Model: {bot.ai_model} · Key: {bot.has_api_key ? '연결됨' : '없음'}</p>
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
