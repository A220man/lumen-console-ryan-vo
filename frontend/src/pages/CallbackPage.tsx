import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LoadingSpinner } from '../components/LoadingSpinner';
 
 export function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code || !state) {
      setError('Missing code or state parameter');
      return;
    }

    const storedVerifier = sessionStorage.getItem('oidc_code_verifier');

    handleCallback({
      code,
      state,
      code_verifier: storedVerifier || '',
    })
      .then(() => navigate('/'))
      .catch((err) => {
        setError(err.message || 'Authentication failed');
      });
  }, [searchParams, navigate, handleCallback]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="card w-full max-w-md text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h1>
          <p className="text-gray-600">{error}</p>
          <button onClick={() => window.location.href = '/login'} className="btn btn-primary mt-4">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md text-center">
        <LoadingSpinner />
        <p className="text-gray-600 mt-4">Completing authentication...</p>
      </div>
    </div>
  );
}