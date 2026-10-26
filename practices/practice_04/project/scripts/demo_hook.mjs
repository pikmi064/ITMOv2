// Invoke the actual plugin handler in an isolated copy; no model is involved.
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
const temporary = await mkdtemp(path.join(tmpdir(), 'practice4-hook-'));
try {
  for (const name of ['server.py', 'deadlines.py', 'mcp_server.py', 'index.html', 'package.json', 'scripts', 'tests', '.opencode']) {
    await cp(path.join(root, name), path.join(temporary, name), { recursive: true });
  }
  const { CheckAfterEdit } = await import(pathToFileURL(path.join(temporary, '.opencode/plugins/check.js')));
  const hooks = await CheckAfterEdit();
  const success = { output: 'Edited index.html in a temporary project copy' };
  await hooks['tool.execute.after']({ tool: 'edit', callID: 'handler-demo-pass' }, success);
  assert.match(success.output, /\[AUTO CHECK PASS\]/);
  const file = path.join(temporary, 'index.html');
  const html = await readFile(file, 'utf8');
  await writeFile(file, html.replace('<script>', '<script>const broken = ;'));
  const failure = { output: 'Introduced invalid JS in the temporary project copy' };
  await hooks['tool.execute.after']({ tool: 'apply_patch', callID: 'handler-demo-fail' }, failure);
  assert.match(failure.output, /\[AUTO CHECK FAIL\]/);
  const ignored = { output: 'Read file' };
  await hooks['tool.execute.after']({ tool: 'read', callID: 'handler-demo-read' }, ignored);
  assert.equal(ignored.output, 'Read file');
  await mkdir(path.join(root, 'output'), { recursive: true });
  await writeFile(path.join(root, 'output/hook-handler-demo.json'), JSON.stringify({
    time: new Date().toISOString(), kind: 'direct handler invocation, not an OpenCode model run',
    pass: success.output, fail: failure.output, readSkipped: true, assertions: 'PASS',
  }, null, 2) + '\n');
  console.log('PASS: hook returns checks after edit; invalid JS returns FAIL; read is skipped');
} finally {
  await rm(temporary, { recursive: true, force: true });
}
