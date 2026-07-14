'use client';

import { useEffect, useState } from 'react';
import { API_URL } from '../lib/api';

export function AsyncPanel<T>({ path, children, fallback }: { path: string; children: (data: T) => React.ReactNode; fallback?: T }) {
  const [data, setData] = useState<T | null>(fallback ?? null);
  const [error, setError] = useState('');
  useEffect(() => {
    fetch(`${API_URL}${path}`)
      .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(setData)
      .catch((e) => setError(`Live API unavailable (${e.message}); displaying repository demo state.`));
  }, [path]);
  return <>{error && <div className="notice">{error}</div>}{data ? children(data) : <div className="loading">Reading inspection state…</div>}</>;
}
