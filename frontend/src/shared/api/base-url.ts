export function getApiBaseUrl(): string {
  const configured = process.env.API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, '');
  }
  return 'http://127.0.0.1:8000';
}
