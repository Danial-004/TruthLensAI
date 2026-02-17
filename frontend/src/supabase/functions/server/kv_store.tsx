// Minimal KV store - application uses localStorage instead
export function set(key: string, value: any): Promise<void> {
  return Promise.resolve();
}

export function get(key: string): Promise<any> {
  return Promise.resolve(null);
}

export function getByPrefix(prefix: string): Promise<any[]> {
  return Promise.resolve([]);
}