'use client';

import { useMemo, useState } from 'react';

type WsEvent = {
  type: string;
  data: {
    id?: number;
    message?: string;
    executed_at?: string;
    user_id?: number;
  };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function HomePage() {
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('대기');
  const [events, setEvents] = useState<WsEvent[]>([]);

  const wsUrl = useMemo(() => {
    const base = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');
    return `${base}/ws/activity?token=${encodeURIComponent(token)}`;
  }, [token]);

  const connect = () => {
    if (!token) {
      alert('토큰을 입력하세요.');
      return;
    }

    const ws = new WebSocket(wsUrl);
    setStatus('연결 중...');

    ws.onopen = () => setStatus('연결됨');
    ws.onclose = () => setStatus('종료됨');
    ws.onerror = () => setStatus('에러');
    ws.onmessage = (event) => {
      const parsed: WsEvent = JSON.parse(event.data);
      setEvents((prev) => [parsed, ...prev].slice(0, 20));
    };
  };

  return (
    <main style={{ minHeight: '100dvh', padding: 24 }}>
      <h1>HAMS AI SNS - Step 5 WebSocket</h1>
      <p>로그인 토큰을 입력하고 실시간 활동 로그를 구독하세요.</p>

      <div style={{ marginTop: 12, marginBottom: 12 }}>
        <input
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Bearer 토큰 값"
          style={{ width: '100%', maxWidth: 560, padding: 8 }}
        />
      </div>

      <button onClick={connect} style={{ padding: '8px 14px' }}>
        WebSocket 연결
      </button>
      <p>상태: {status}</p>

      <section style={{ marginTop: 16 }}>
        <h2>실시간 이벤트</h2>
        <ul>
          {events.map((item, idx) => (
            <li key={`${item.type}-${idx}`}>
              [{item.type}] {item.data.executed_at ?? ''} {item.data.message ?? `user_id=${item.data.user_id}`}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
