#!/usr/bin/env node
// Generates lib/db-data.ts with the SQLite database AND sql.js WASM binary
// as base64 strings. Used in CI to embed both into the Cloudflare Worker bundle.

const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname, '..', '..', 'data', 'social.db');
const wasmPath = path.join(__dirname, '..', 'node_modules', 'sql.js', 'dist', 'sql-wasm.wasm');
const outPath = path.join(__dirname, '..', 'lib', 'db-data.ts');

if (!fs.existsSync(dbPath)) {
  console.error('Database not found at', dbPath);
  process.exit(1);
}

if (!fs.existsSync(wasmPath)) {
  console.error('sql.js WASM not found at', wasmPath);
  process.exit(1);
}

const db = fs.readFileSync(dbPath);
const dbB64 = db.toString('base64');

const wasm = fs.readFileSync(wasmPath);
const wasmB64 = wasm.toString('base64');

fs.writeFileSync(outPath,
  `// Auto-generated — do not edit\n` +
  `export const DB_BASE64: string = '${dbB64}'\n` +
  `export const WASM_BASE64: string = '${wasmB64}'\n`
);

console.log(`Generated db-data.ts: DB ${dbB64.length} chars (${db.length} bytes), WASM ${wasmB64.length} chars (${wasm.length} bytes)`);
