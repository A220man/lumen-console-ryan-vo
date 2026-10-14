export function LoadingSpinner() {
  return (
    <div className="loading" role="status" aria-label="Loading">
      <div className="spinner" data-testid="spinner-element" />
    </div>
  );
}