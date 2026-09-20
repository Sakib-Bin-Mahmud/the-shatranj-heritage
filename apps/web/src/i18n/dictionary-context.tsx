"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { defaultLocale, locales, type Locale } from "./config";
import { getDictionary, type Dictionary } from "./get-dictionary";
import enDictionary from "./dictionaries/en.json";

const LOCALE_STORAGE_KEY = "shatranj_locale";

type DictionaryContextValue = {
  locale: Locale;
  dict: Dictionary;
  setLocale: (locale: Locale) => void;
};

const DictionaryContext = createContext<DictionaryContextValue | null>(null);

function readStoredLocale(): Locale {
  if (typeof window === "undefined") return defaultLocale;
  try {
    const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    return locales.includes(stored as Locale)
      ? (stored as Locale)
      : defaultLocale;
  } catch {
    return defaultLocale;
  }
}

function storeLocale(locale: Locale) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Ignore storage failures (private browsing, quota, etc.) — the
    // page still works, it just won't remember the choice next visit.
  }
}

export function DictionaryProvider({ children }: { children: ReactNode }) {
  // Always English on first render, matching the static/server-rendered
  // shell (which has no access to localStorage) — same hydration-safety
  // reasoning as AuthProvider's `status` initializer in auth-context.tsx.
  // Swapping to a stored non-default locale happens in the effect below,
  // post-hydration, not in this initializer.
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [dict, setDict] = useState<Dictionary>(enDictionary);

  useEffect(() => {
    const stored = readStoredLocale();
    if (stored !== defaultLocale) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocaleState(stored);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    getDictionary(locale).then((next) => {
      if (!cancelled) setDict(next);
    });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  // WCAG 3.1.1 (Language of Page): the server-rendered shell always
  // ships `lang="en"` (see layout.tsx — a Server Component has no
  // access to this client-only locale preference), so keep it in sync
  // here once a locale is actually known/changed.
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    storeLocale(next);
  }, []);

  return (
    <DictionaryContext.Provider value={{ locale, dict, setLocale }}>
      {children}
    </DictionaryContext.Provider>
  );
}

export function useDictionary(): DictionaryContextValue {
  const context = useContext(DictionaryContext);
  if (!context) {
    throw new Error("useDictionary must be used within a DictionaryProvider");
  }
  return context;
}
