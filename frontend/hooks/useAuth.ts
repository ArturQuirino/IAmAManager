'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/api';

export function useAuth(redirectToLogin = true) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token && redirectToLogin) {
      router.replace('/login');
      setIsAuthenticated(false);
    } else {
      setIsAuthenticated(!!token);
    }
  }, [router, redirectToLogin]);

  return { isAuthenticated };
}

export function useRedirectIfAuthenticated() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.replace('/home');
    }
  }, [router]);
}
