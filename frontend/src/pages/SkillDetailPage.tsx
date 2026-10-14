import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Skill } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (id) {
      fetchSkill();
    }
  }, [id]);

  const fetchSkill = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSkill(id);
      setSkill(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skill');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!id) return;
    setUpdating(true);
    try {
      await api.updateSkill(id);
      await fetchSkill();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setUpdating(false);
    }
  };

  const handleCheckUpdate = async () => {
    if (!id) return;
    try {
      const result = await api.checkSkillUpdate(id);
      if (result.update_available) {
        alert('Update available!');
      } else {
        alert('Skill is up to date');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Check failed');
    }
  };

  if (loading) return <LoadingSpinner />;

  if (error && !skill) {
    return (
      <div className="error-message" role="alert">
        {error}
        <Link to="/skills" className="btn btn-primary mt-4 inline-block">
          Back to Skills
        </Link>
      </div>
    );
  }

  if (!skill) return null;

  let meta: { description?: string; tags?: string[]; content?: string; version?: string; author?: string } = {};
  try {
    meta = JSON.parse(skill.skill_metadata || '{}');
  } catch {}

  return (
    <div>
      <header className="page-header flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="page-title">{skill.name}</h1>
          <p className="page-description">
            {skill.source_url.split('/').slice(-2).join('/')} • {skill.skill_path}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/skills" className="btn btn-secondary">
            ← Back to Skills
          </Link>
        </div>
      </header>

      {error && <div className="error-message mb-6" role="alert">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="card">
            <h2 className="text-lg font-semibold mb-4">Description</h2>
            {meta.description ? (
              <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
                {meta.description}
              </div>
            ) : (
              <p className="text-gray-500 italic">No description available</p>
            )}
          </section>

          {meta.content && (
            <section className="card">
              <h2 className="text-lg font-semibold mb-4">Skill Content</h2>
              <div className="bg-gray-50 p-4 rounded font-mono text-sm whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                {meta.content}
              </div>
            </section>
          )}

          <section className="card">
            <h2 className="text-lg font-semibold mb-4">Metadata</h2>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <dt className="text-gray-500">Version</dt>
              <dd className="font-medium">{meta.version || '1.0.0'}</dd>
              <dt className="text-gray-500">Author</dt>
              <dd className="font-medium">{meta.author || 'Unknown'}</dd>
              <dt className="text-gray-500">Source Type</dt>
              <dd className="font-medium">{skill.source_type}</dd>
              <dt className="text-gray-500">Folder Hash</dt>
              <dd className="font-mono text-xs break-all">{skill.skill_folder_hash}</dd>
              <dt className="text-gray-500">Status</dt>
              <dd className="font-medium capitalize">{skill.status}</dd>
              <dt className="text-gray-500">Scope</dt>
              <dd className="font-medium capitalize">{skill.scope}</dd>
              <dt className="text-gray-500">Installed</dt>
              <dd className="font-medium">
                {skill.installed_at ? new Date(skill.installed_at).toLocaleDateString() : 'N/A'}
              </dd>
              <dt className="text-gray-500">Updated</dt>
              <dd className="font-medium">
                {new Date(skill.updated_at).toLocaleDateString()}
              </dd>
            </dl>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card">
            <h2 className="text-lg font-semibold mb-4">Actions</h2>
            <div className="space-y-3">
              <button
                onClick={handleUpdate}
                disabled={updating}
                className="btn btn-primary w-full"
              >
                {updating ? 'Updating...' : 'Update Skill'}
              </button>
              <button
                onClick={handleCheckUpdate}
                disabled={updating}
                className="btn btn-secondary w-full"
              >
                Check for Updates
              </button>
              <button className="btn btn-danger w-full">
                Uninstall
              </button>
            </div>
          </section>

          <section className="card">
            <h2 className="text-lg font-semibold mb-4">Tags</h2>
            {meta.tags && Array.isArray(meta.tags) && meta.tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {(meta.tags as string[]).map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No tags</p>
            )}
          </section>

          <section className="card">
            <h2 className="text-lg font-semibold mb-4">Installation Path</h2>
            <p className="font-mono text-sm text-gray-600 break-all bg-gray-50 p-2 rounded">
              {skill.target_path || 'Not available'}
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}