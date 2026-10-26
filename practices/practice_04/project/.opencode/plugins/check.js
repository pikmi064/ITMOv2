import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { appendFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const execute = promisify(execFile);
const root = fileURLToPath(new URL('../../', import.meta.url));

export const CheckAfterEdit = async () => ({
  'tool.execute.after': async (input, output) => {
    if (!['write', 'edit', 'apply_patch'].includes(input.tool)) return;
    let status = 'PASS', report;
    try {
      const result = await execute('python3', ['scripts/check.py'], {
        cwd: root, timeout: 45000, maxBuffer: 256 * 1024,
      });
      report = result.stdout + result.stderr;
    } catch (error) {
      status = 'FAIL';
      report = (error.stdout || '') + (error.stderr || '') + '\n' + error.message;
    }
    const message = `\n\n[AUTO CHECK ${status}]\n${report}`;
    output.output = (output.output || '') + message;
    const folder = path.join(root, 'output');
    try {
      await mkdir(folder, { recursive: true });
      await appendFile(path.join(folder, 'hooks.jsonl'), JSON.stringify({
        time: new Date().toISOString(), tool: input.tool,
        callID: input.callID, status, report,
      }) + '\n');
    } catch (error) {
      output.output += `\nCould not save hook evidence: ${error.message}`;
    }
  },
});
