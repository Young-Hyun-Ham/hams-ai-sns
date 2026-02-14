import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, '..');
const localNextBin = path.join(frontendRoot, 'node_modules', '.bin', process.platform === 'win32' ? 'next.cmd' : 'next');

function run(cmd, args) {
  const result = spawnSync(cmd, args, {
    stdio: 'inherit',
    cwd: frontendRoot,
    shell: process.platform === 'win32'
  });
  return result.status ?? 1;
}

if (existsSync(localNextBin)) {
  process.exit(run(localNextBin, ['build']));
}

console.warn('[hams-frontend] local next binary를 찾지 못했습니다.');
console.warn('[hams-frontend] node_modules 미설치 환경으로 판단하여 npx fallback을 시도합니다.');

const fallbackStatus = run('npx', ['--yes', 'next@14.2.5', 'build']);
if (fallbackStatus !== 0) {
  console.error('[hams-frontend] 빌드 실패: 아래 명령으로 의존성 설치 후 다시 시도하세요.');
  console.error('  npm install');
  console.error('  npm run build');
}

process.exit(fallbackStatus);
