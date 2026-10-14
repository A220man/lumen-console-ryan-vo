import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Skill, SkillListResponse, SkillSearchResult } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [searchResults, setSearchResults] = useState<SkillSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOwner, setSearchOwner] = useState('');
  const [activeTab, setActiveTab] = useState<'installed' | 'search'>('installed');
  const pageSize = 20;

  useEffect(() => {
    if (activeTab === 'installed') {
      fetchSkills();
    }
  }, [activeTab, page]);

  const fetchSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const data: SkillListResponse = await api.listSkills({ page, page_size: pageSize });
      setSkills(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);
    try {
      const results = await api.searchSkills({
        q: searchQuery,
        owner: searchOwner || undefined,
        limit: 20,
      });
      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Skills</h1>
        <p className="page-description">Manage and discover agent skills</p>
      </header>

      <div className="card mb-6">
        <div className="border-b border-gray-200 mb-4">
          <nav className="flex gap-6" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'installed'}
              onClick={() => setActiveTab('installed')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${activeTab === 'installed' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              Installed Skills
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'search'}
              onClick={() => setActiveTab('search')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${activeTab === 'search' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              Search & Discover
            </button>
          </nav>
        </div>

        {activeTab === 'search' && (
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search-query" className="form-label">Search Query</label>
              <input
                id="search-query"
                type="text"
                className="form-input"
                placeholder="Search skills by name, description, tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="w-full sm:w-64">
              <label htmlFor="search-owner" className="form-label">Filter by Owner (optional)</label>
              <input
                id="search-owner"
                type="text"
                className="form-input"
                placeholder="e.g., vercel-labs"
                value={searchOwner}
                onChange={(e) => setSearchOwner(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="btn btn-primary self-end"
            >
              {searching ? 'Searching...' : 'Search'}
            </button>
          </form>
        )}
      </div>

      {error && (
        <div className="error-message" role="alert">{error}</div>
      )}

      {activeTab === 'installed' ? (
        <InstalledSkillsView
          skills={skills}
          loading={loading}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      ) : (
        <SearchResultsView results={searchResults} loading={searching} />
      )}
    </div>
  );
}

function InstalledSkillsView({
  skills,
  loading,
  page,
  totalPages,
  onPageChange,
}: {
  skills: Skill[];
  loading: boolean;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (loading) return <LoadingSpinner />;

  if (skills.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📦</div>
        <p>No skills installed in this scope</p>
        <p className="text-sm mt-2">Install skills from GitHub repositories or restore from lock file</p>
        <div className="flex gap-2 justify-center mt-4 flex-wrap">
          <Link to="/skills" className="btn btn-primary">Install from GitHub</Link>
          <button className="btn btn-secondary">Restore from Lock File</button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="skills-grid">
        {skills.map((skill) => (
          <SkillCard key={skill.id} skill={skill} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="btn btn-secondary"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className="btn btn-secondary"
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}

function SearchResultsView({
  results,
  loading,
}: {
  results: SkillSearchResult[];
  loading: boolean;
}) {
  if (loading) return <LoadingSpinner />;

  if (results.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🔍</div>
        <p>No skills found matching your search</p>
        <p className="text-sm mt-2">Try different keywords or check the owner filter</p>
      </div>
    );
  }

  return (
    <div className="skills-grid">
      {results.map((skill) => (
        <SearchResultCard key={skill.id} skill={skill} />
      ))}
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
        <p className="skill-description">{meta.description}</p>
      )}
      {meta.tags && Array.isArray(meta.tags) && meta.tags.length > 0 && (
        <div className="skill-tags">
          {meta.tags.slice(0, 4).map((tag) => (
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

function SearchResultCard({ skill }: { skill: SkillSearchResult }) {
  return (
    <div className="skill-card">
      <h3 className="skill-name">{skill.name}</h3>
      <p className="skill-source">{skill.owner}/{skill.name}</p>
      {skill.description && (
        <p className="skill-description">{skill.description}</p>
      )}
      {skill.tags.length > 0 && (
        <div className="skill-tags">
          {skill.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}
      <div className="skill-actions">
        <button className="btn btn-primary text-xs flex-1">
          Install
        </button>
      </div>
    </div>
  );
}