import { useState, useEffect, useCallback } from 'react';

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('docgen-theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('docgen-theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }, []);

  return { theme, toggleTheme };
}

export function usePolling(fetchFn, interval = 3000, enabled = true) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!enabled) return;

    let timer;
    let mounted = true;

    const poll = async () => {
      try {
        const result = await fetchFn();
        if (mounted) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err);
          setLoading(false);
        }
      }
    };

    poll();
    timer = setInterval(poll, interval);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [fetchFn, interval, enabled]);

  return { data, error, loading };
}
