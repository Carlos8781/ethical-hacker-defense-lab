#!/usr/bin/env node
/** Run npm's built-in audit only against the project you administer. */
const { spawnSync } = require('node:child_process');

if (process.argv.includes('--help')) {
  console.log('Usage: node node/dependency-audit.js [path-to-project]');
  console.log('Runs npm audit --json in an authorized local Node.js project.');
  process.exit(0);
}

const project = process.argv[2] || process.cwd();
const result = spawnSync('npm', ['audit', '--json'], {
  cwd: project,
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
});

if (result.error) {
  console.error(`Could not run npm audit: ${result.error.message}`);
  process.exit(2);
}
process.stdout.write(result.stdout || result.stderr);
process.exit(result.status ?? 2);
