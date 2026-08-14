// React는 Django API만 호출합니다. FastAPI는 Django 서버 내부에서만 호출됩니다.
export const DJANGO_BASE_URL = (import.meta.env.VITE_DJANGO_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

let csrfToken = null;

async function loadCsrfToken() {
  const response = await fetch(`${DJANGO_BASE_URL}/api/members/csrf/`, {
    method: 'GET',
    credentials: 'include',
  });
  if (!response.ok) throw new Error('CSRF 토큰을 가져오지 못했습니다.');
  const data = await response.json();
  csrfToken = data.csrfToken;
  return csrfToken;
}

export function resolveDjangoUrl(url) {
  if (!url) return '';
  if (/^https?:\/\//i.test(url)) return url;
  return `${DJANGO_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;
}

export async function apiFetch(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const token = csrfToken || await loadCsrfToken();
    headers.set('X-CSRFToken', token);
  }

  const response = await fetch(`${DJANGO_BASE_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
  });

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const error = new Error(data?.message || data?.detail || data || `HTTP ${response.status}`);
    error.status = response.status;
    error.data = data;
    if (response.status === 403) csrfToken = null;
    throw error;
  }
  return data;
}

export function toFormData(values) {
  const formData = new FormData();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') formData.append(key, value);
  });
  return formData;
}
