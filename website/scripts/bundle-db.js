#!/usr/bin/env node
// Generates lib/db-data.ts with the SQLite database as a base64 string.
// Used in CI to embed the database into the Cloudflare Worker bundle.

const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname, '..', '..', 'data', 'social.db');
const outPath = path.join(__dirname, '..', 'lib', 'db-data.ts');

if (!fs.existsSync(dbPath)) {
  console.error('Database not found at', dbPath);
  process.exit(1);
}

const db = fs.readFileSync(dbPath);
const b64 = db.toString('base64');

fs.writeFileSync(outPath,
  `// Auto-generated — do not edit\nexport const DB_BASE64: string = '${b64}'\n`
);

console.log(`Generated db-data.ts: ${b64.length} chars base64 from ${db.length} bytes DB`);
