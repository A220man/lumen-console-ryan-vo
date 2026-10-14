import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { LockFile } from '../types';
import { useAuth } from '../hooks/useAuth';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function SettingsPage() {
  const { user } = useAuth();
  const [projectLock, setProjectLock] = useState<LockFile | null>(null);
  const [globalLock, setGlobalLock] = useState<LockFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState<'project' | 'global' | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLockFiles();
  }, []);

  const fetchLockFiles = async () => {
    setLoading(true);
    try {
      const [project, global] = await Promise.all([
        api.getLockFile('project').catch(() => null),
        api.getLockFile('global').catch(() => null),
      ]);
      setProjectLock(project);
      setGlobalLock(global);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleInstallFromLock = async (scope: 'project' | 'global') => {
    setInstalling(scope);
    setError(null);
    try {
      await api.installFromLock({ scope, force: false });
      alert(`${scope} skills restored from lock file`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Install failed');
    } finally {
      setInstalling(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-description">Manage your account, lock files, and preferences</p>
      </header>

      {error && <div className="error-message mb-6" role="alert">{error}</div>}

      <section className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Account</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <dt className="text-gray-500">Name</dt>
          <dd className="font-medium">{user?.name || 'Not set'}</dd>
          <dt className="text-gray-500">Email</dt>
          <dd className="font-medium">{user?.email || 'Not set'}</dd>
          <dt className="text-gray-500">Username</dt>
          <dd className="font-medium">{user?.preferred_username || 'Not set'}</dd>
          <dt className="text-gray-500">Subject ID</dt>
          <dd className="font-mono text-sm break-all">{user?.sub}</dd>
          <dt className="text-gray-500">Roles</dt>
          <dd className="font-medium">{user?.roles.join(', ') || 'None'}</dd>
        </dl>
      </section>

      <section className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Lock Files</h2>
        <p className="text-gray-600 mb-4">
          Lock files track installed skills for reproducible installs. Use <code>skills install</code> (or <code>skills ci</code>)
          to restore all skills from the lock file on a new machine or in CI.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <LockFileCard
            title="Project Lock File"
            lock={projectLock}
            installing={installing === 'project'}
            onInstall={() => handleInstallFromLock('project')}
          />
          <LockFileCard
            title="Global Lock File"
            lock={globalLock}
            installing={installing === 'global'}
            onInstall={() => handleInstallFromLock('global')}
          />
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-4">About</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <dt className="text-gray-500">Version</dt>
          <dd className="font-medium">1.0.0</dd>
          <dt className="text-gray-500">API Base</dt>
          <dd className="font-mono text-xs break-all">{import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'}</dd>
          <dt className="text-gray-500">OIDC Issuer</dt>
          <dd className="font-mono text-xs break-all">{import.meta.env.VITE_OIDC_ISSUER || 'http://127.0.0.1:8080/realms/lumen'}</dd>
        </dl>
      </section>
    </div>
  );
}

function LockFileCard({
  title,
  lock,
  installing,
  onInstall,
}: {
  title: string;
  lock: LockFile | null;
  installing: boolean;
  onInstall: () => void;
}) {
  const skillCount = lock ? Object.keys(lock.skills).length : 0;

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-4">
        {skillCount} skill{skillCount !== 1 ? 's' : ''} tracked
      </p>

      {lock && (
        <details className="mb-4">
          <summary className="text-sm text-blue-600 hover:underline cursor-pointer">
            View lock file contents
          </summary>
          <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto max-h-48">
            {JSON.stringify(lock.skills, null, 2)}
          </pre>
        </details>
      )}

      <button
        onClick={onInstall}
        disabled={!lock || installing}
        className="btn btn-primary w-full"
      >
        {installing ? 'Installing...' : lock ? 'Restore Skills (skills install)' : 'No lock file found'}
      </button>

      {lock && (
        <button
          className="btn btn-secondary w-full mt-2"
          onClick={() => onInstall()}
        >
          Force Reinstall (skills ci)
        </button>
      )}
    </div>
  );
}