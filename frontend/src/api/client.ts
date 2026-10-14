import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { Skill, SkillListResponse, SkillSearchResult, InstallRequest, InstallResponse, LockFile, LockInstallRequest, User, HealthResponse, AuthURLResponse, CallbackRequest, TokenResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE}/api/v1`,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => config,
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - redirect to login
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async getAuthUrl(redirectUri?: string): Promise<AuthURLResponse> {
    const response = await this.client.get<AuthURLResponse>('/auth/login', {
      params: { redirect_uri: redirectUri },
    });
    return response.data;
  }

  async callback(data: CallbackRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/callback', data);
    return response.data;
  }

  async logout(idTokenHint?: string): Promise<{ logout_url: string }> {
    const response = await this.client.post<{ logout_url: string }>('/auth/logout', null, {
      params: { id_token_hint: idTokenHint },
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  async listSkills(params: {
    page?: number;
    page_size?: number;
    scope?: 'project' | 'global';
    status?: string;
  } = {}): Promise<SkillListResponse> {
    const response = await this.client.get<SkillListResponse>('/skills', { params });
    return response.data;
  }

  async searchSkills(params: {
    q: string;
    owner?: string;
    limit?: number;
    offset?: number;
  }): Promise<SkillSearchResult[]> {
    const response = await this.client.get<SkillSearchResult[]>('/skills/search', { params });
    return response.data;
  }

  async getSkill(id: string): Promise<Skill> {
    const response = await this.client.get<Skill>(`/skills/${id}`);
    return response.data;
  }

  async installSkill(data: InstallRequest): Promise<InstallResponse> {
    const response = await this.client.post<InstallResponse>('/skills/install', data);
    return response.data;
  }

  async updateSkill(id: string, force = false): Promise<{ message: string; skill: Skill }> {
    const response = await this.client.post<{ message: string; skill: Skill }>(`/skills/${id}/update`, { force });
    return response.data;
  }

  async checkSkillUpdate(id: string): Promise<{ skill_id: string; update_available: boolean }> {
    const response = await this.client.get<{ skill_id: string; update_available: boolean }>(`/skills/${id}/check-update`);
    return response.data;
  }

  async getLockFile(scope: 'project' | 'global' = 'project'): Promise<LockFile> {
    const response = await this.client.get<LockFile>('/lock', { params: { scope } });
    return response.data;
  }

  async installFromLock(data: LockInstallRequest): Promise<{ results: Array<{ name: string; status: string; error?: string }> }> {
    const response = await this.client.post<{ results: Array<{ name: string; status: string; error?: string }> }>('/lock/install', data);
    return response.data;
  }
}

export const api = new ApiClient();