import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { HealthResponse, Skill } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';

export function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [recentSkills, setRecentSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthData, skillsData] = await Promise.all([
          api.health(),
          api.listSkills({ page: 1, page_size: 5 }),
        ]);
        setHealth(healthData);
        setRecentSkills(skillsData.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="error-message" role="alert">
        {error}
      </div>
    );
  }

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">Welcome back, {user?.name || user?.preferred_username || 'User'}</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Health Status</h3>
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="capitalize">{health?.status || 'unknown'}</span>
          </div>
          <p className="text-sm text-gray-600 mt-1">Version: {health?.version}</p>
          <p className="text-sm text-gray-600">Demo mode: {health?.demo_mode ? 'Yes' : 'No'}</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Installed Skills</h3>
          <p className="text-3xl font-bold text-blue-600">{recentSkills.length}</p>
          <p className="text-sm text-gray-600">Total in current scope</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Quick Actions</h3>
          <div className="space-y-2">
            <Link to="/skills" className="btn btn-primary w-full justify-center">
              Browse Skills
            </Link>
            <Link to="/skills" className="btn btn-secondary w-full justify-center">
              Install from Lock File
            </Link>
          </div>
        </div>
      </div>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recently Installed Skills</h2>
          <Link to="/skills" className="text-sm text-blue-600 hover:underline">
            View All
          </Link>
        </div>

        {recentSkills.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📦</div>
            <p>No skills installed yet</p>
            <Link to="/skills" className="btn btn-primary mt-4 inline-flex">
              Install Your First Skill
            </Link>
          </div>
        ) : (
          <div className="skills-grid">
            {recentSkills.map((skill) => (
              <SkillCard key={skill.id} skill={skill} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function SkillCard({ skill }: { skill: Skill }) {
  let meta: { description?: string; tags?: string[] } = {};
  try {
    meta = JSON.parse(skill.skill_metadata || '{}');
  } catch {}

  return (
    <Link to={`/skills/${skill.id}`} className="skill-card">
      <h3 className="skill-name">{skill.name}</h3>
      <p className="skill-source">
        {skill.source_url.split('/').slice(-2).join('/')}
        <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full capitalize">
          {skill.scope}
        </span>
      </p>
      {meta.description && (
        <p className="skill-description">{meta.description as string}</p>
      )}
      {meta.tags && Array.isArray(meta.tags) && meta.tags.length > 0 && (
        <div className="skill-tags">
          {(meta.tags as string[]).slice(0, 4).map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}
      <div className="skill-actions">
        <span className="btn btn-secondary text-xs flex-1 justify-center">
          View Details
        </span>
      </div>
    </Link>
  );
}