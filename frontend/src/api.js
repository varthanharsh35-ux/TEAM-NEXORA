export async function api(path, body, signal) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort);
  try {
    const response = await fetch(`/api${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail || data;
      throw Object.assign(
        new Error(typeof detail === 'string' ? detail : detail.error || 'invalid_input'),
        { detail }
      );
    }
    return data;
  } catch (e) {
    if (!e.detail) throw Object.assign(new Error('server_error'), { cause: e });
    throw e;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
  }
}
export function restore(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    if (value == null) return fallback;
    if (Array.isArray(fallback) && !Array.isArray(value)) return fallback;
    if (
      fallback &&
      typeof fallback === 'object' &&
      !Array.isArray(fallback) &&
      (typeof value !== 'object' || Array.isArray(value))
    )
      return fallback;
    return value;
  } catch {
    return fallback;
  }
}
export function persist(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}
