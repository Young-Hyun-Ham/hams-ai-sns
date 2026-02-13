'use client';

import { create } from 'zustand';

type ThemeMode = 'light' | 'dark';

type ThemeState = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: 'light',
  setMode: (mode) => set({ mode }),
  toggleMode: () => set({ mode: get().mode === 'light' ? 'dark' : 'light' })
}));
