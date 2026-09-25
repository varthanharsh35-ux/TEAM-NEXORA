import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const value = process.env.BACKEND_ORIGIN;
if (!value) throw new Error('Set BACKEND_ORIGIN to the HTTPS origin of your persistent backend. See docs/DEPLOYMENT.md.');
const backend = new URL(value);
if (backend.protocol !== 'https:' || backend.username || backend.password || backend.search || backend.hash || backend.pathname !== '/') {
  throw new Error('BACKEND_ORIGIN must be an HTTPS origin without credentials, a path, query, or fragment.');
}
const output = path.join(root, '.vercel/output');
fs.mkdirSync(output, { recursive: true });
fs.cpSync(path.join(root, 'frontend/dist'), path.join(output, 'static'), { recursive: true });
fs.writeFileSync(path.join(output, 'config.json'), JSON.stringify({
  version: 3,
  routes: [
    { src: '/api(?:/(.*))?$', dest: `${backend.origin}/api/$1`, headers: { 'Cache-Control': 'no-store' } },
    { src: '/(?:sw\\.js|index\\.html)?$', headers: { 'Cache-Control': 'no-cache' }, continue: true },
    { handle: 'filesystem' },
    { src: '/.*', dest: '/index.html' },
  ],
}, null, 2) + '\n');
console.log('Vercel frontend output ready; API requests use the configured persistent backend.');
