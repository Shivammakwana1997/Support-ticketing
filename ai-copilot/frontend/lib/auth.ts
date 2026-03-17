import { api } from './api';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '@/types/user';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function setRefreshToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getUserFromToken(): User | null {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      role: payload.role,
      is_active: true,
      created_at: '',
      updated_at: '',
    };
  } catch {
    return null;
  }
}

export async function login(credentials: LoginRequest): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/v1/auth/login', credentials);
  setToken(response.access_token);
  setRefreshToken(response.refresh_token);
  return response;
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/v1/auth/register', data);
  setToken(response.access_token);
  setRefreshToken(response.refresh_token);
  return response;
}

export async function refreshAuth(): Promise<AuthResponse> {
  const refreshToken = typeof window !== 'undefined' ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
  const response = await api.post<AuthResponse>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  });
  setToken(response.access_token);
  setRefreshToken(response.refresh_token);
  return response;
}

export async function getMe(): Promise<User> {
  return api.get<User>('/api/v1/auth/me');
}

export function logout(): void {
  removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}
