import { create } from "zustand";

interface LoginFormState {
  serverError: string | null;
  rememberMe: boolean;
}

interface LoginFormActions {
  setServerError: (error: string | null) => void;
  setRememberMe: (remember: boolean) => void;
  reset: () => void;
}

const initialState: LoginFormState = {
  serverError: null,
  rememberMe: false,
};

export const useLoginFormStore = create<LoginFormState & LoginFormActions>()(
  (set) => ({
    ...initialState,
    setServerError: (error) => set({ serverError: error }),
    setRememberMe: (remember) => set({ rememberMe: remember }),
    reset: () => set(initialState),
  }),
);
