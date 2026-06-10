"use client";

/**
 * Session store (Zustand + localStorage persistence).
 *
 * Holds the JWT and the resolved `me` context (user + active organization +
 * role). Components read narrow slices; the dashboard layout guards access.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/types";

interface SessionState {
  token: string | null;
  me: Me | null;
  error: string | null;
  loading: boolean;

  login: (email: string, password: string) => Promise<boolean>;
  register: (input: {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
  }) => Promise<boolean>;
  refreshMe: () => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useSession = create<SessionState>()(
  persist(
    (set, get) => ({
      token: null,
      me: null,
      error: null,
      loading: false,

      login: async (email, password) => {
        set({ loading: true, error: null });
        try {
          const token = await api.login(email, password);
          const me = await api.me(token);
          set({ token, me, loading: false });
          return true;
        } catch (err) {
          set({
            loading: false,
            error: err instanceof ApiError ? err.message : "Login failed",
          });
          return false;
        }
      },

      register: async (input) => {
        set({ loading: true, error: null });
        try {
          await api.register(input);
          const token = await api.login(input.email, input.password);
          const me = await api.me(token);
          set({ token, me, loading: false });
          return true;
        } catch (err) {
          set({
            loading: false,
            error: err instanceof ApiError ? err.message : "Registration failed",
          });
          return false;
        }
      },

      refreshMe: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const me = await api.me(token);
          set({ me });
        } catch {
          // Token invalid/expired — drop the session.
          set({ token: null, me: null });
        }
      },

      logout: () => set({ token: null, me: null, error: null }),
      clearError: () => set({ error: null }),
    }),
    {
      name: "saas-analytics-session",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, me: state.me }),
    },
  ),
);
