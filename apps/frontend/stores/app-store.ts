'use client';

import { create } from 'zustand';

import { getStorageAdapter } from '../lib/storage/adapter';

const TOKEN_KEY = 'hams_access_token';
const THEME_KEY = 'hams_theme';

type ThemeMode = 'light' | 'dark';

type AppState = {
  mode: ThemeMode;
  accessToken: string;
  hydrate: () => void;
  toggleMode: () => void;
  setAccessToken: (token: string) => void;
  clearAccessToken: () => void;
};

export const useAppStore = create<AppState>((set, get) => ({
  mode: 'light',
  accessToken: '',
  hydrate: () => {
    const storage = getStorageAdapter();
    const savedTheme = storage.getItem(THEME_KEY);
    const savedToken = storage.getItem(TOKEN_KEY);

    set({
      mode: savedTheme === 'dark' ? 'dark' : 'light',
      accessToken: savedToken ?? ''
    });
  },
  toggleMode: () => {
    const storage = getStorageAdapter();
    const next = get().mode === 'light' ? 'dark' : 'light';
    storage.setItem(THEME_KEY, next);
    set({ mode: next });
  },
  setAccessToken: (token) => {
    const storage = getStorageAdapter();
    storage.setItem(TOKEN_KEY, token);
    set({ accessToken: token });
  },
  clearAccessToken: () => {
    const storage = getStorageAdapter();
    storage.removeItem(TOKEN_KEY);
    set({ accessToken: '' });
  }
}));
