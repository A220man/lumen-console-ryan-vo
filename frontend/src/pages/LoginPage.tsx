import { useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function LoginPage() {
  const { login, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      login();
    }
  }, [login, loading]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md text-center">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">lumen-console</h1>
          <p className="text-gray-600 mt-2">Open Agent Skills Management</p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-4">
            <p className="text-gray-600">Redirecting to Keycloak for authentication...</p>
            <div className="spinner mx-auto" data-testid="spinner" />
          </div>
        )}
      </div>
    </div>
  );
}