import axios from 'axios';

const TOKEN_KEY = 'trendit_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function apiLogin(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const { data } = await axios.post('/api/auth/jwt/login', body.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data.access_token;
}

export async function apiRegister(email: string, password: string): Promise<void> {
  await axios.post('/api/auth/register', { email, password });
}

export async function apiLogout(token: string): Promise<void> {
  await axios.post('/api/auth/jwt/logout', null, {
    headers: { Authorization: `Bearer ${token}` },
  });
  clearToken();
}
