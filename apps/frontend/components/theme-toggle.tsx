'use client';

import { useEffect } from 'react';
import DarkModeOutlined from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlined from '@mui/icons-material/LightModeOutlined';

import { useThemeStore } from '../stores/theme-store';

export function ThemeToggle() {
  const mode = useThemeStore((s) => s.mode);
  const toggleMode = useThemeStore((s) => s.toggleMode);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', mode === 'dark');
  }, [mode]);

  return (
    <button
      type="button"
      onClick={toggleMode}
      className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm"
    >
      {mode === 'dark' ? <LightModeOutlined fontSize="small" /> : <DarkModeOutlined fontSize="small" />}
      {mode === 'dark' ? '라이트 모드' : '다크 모드'}
    </button>
  );
}
