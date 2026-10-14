export interface Skill {
  id: string;
  owner_id: string;
  name: string;
  source_url: string;
  source_type: string;
  skill_path: string;
  skill_folder_hash: string;
  scope: 'project' | 'global';
  status: 'pending' | 'installed' | 'updating' | 'failed';
  target_path: string | null;
  skill_metadata: string;
  installed_at: string | null;
  updated_at: string;
  created_at: string;
}

export interface SkillListResponse {
  items: Skill[];
  total: number;
  page: number;
  page_size: number;
}

export interface SkillSearchResult {
  id: string;
  name: string;
  owner: string;
  description: string | null;
  source_url: string;
  tags: string[];
}

export interface InstallRequest {
  source_url: string;
  skill_name: string;
  skill_path?: string;
  scope: 'project' | 'global';
  force?: boolean;
}

export interface InstallResponse {
  skill: Skill;
  lock_file_updated: boolean;
}

export interface LockFile {
  version: string;
  skills: Record<string, LockSkill>;
  dismissed: Record<string, boolean>;
  updated_at: string;
}

export interface LockSkill {
  source: string;
  sourceType: string;
  sourceUrl: string;
  skillPath: string;
  skillFolderHash: string;
  installedAt: string;
  updatedAt: string;
}

export interface LockInstallRequest {
  scope: 'project' | 'global';
  force?: boolean;
}

export interface User {
  id: string;
  sub: string;
  email: string | null;
  name: string | null;
  preferred_username: string | null;
  roles: string[];
  created_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  demo_mode: boolean;
}

export interface AuthURLResponse {
  auth_url: string;
  state: string;
  nonce: string;
  code_verifier: string;
}

export interface CallbackRequest {
  code: string;
  state: string;
  code_verifier: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
}