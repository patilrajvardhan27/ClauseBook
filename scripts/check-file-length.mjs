#!/usr/bin/env node
// Fails CI when a source file passes 250 lines. Generated code, lockfiles
// and fixtures are excluded because they are not something a person edits
// by hand, so a line-count ceiling on them would just be noise.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const LIMIT = 250;
const SOURCE_EXTENSIONS = new Set([".py", ".ts", ".tsx", ".js", ".jsx"]);
const EXCLUDED_DIR_SEGMENTS = [
  "node_modules", ".venv", "dist", "build", "versions", ".git",
  "contracts/openapi", "eval/fixtures", "coverage",
];
const EXCLUDED_FILE_SUFFIXES = [".generated.ts", ".generated.tsx", ".lock", ".min.js"];

function isExcludedDir(path) {
  return EXCLUDED_DIR_SEGMENTS.some((segment) => path.includes(segment));
}

function isExcludedFile(path) {
  return EXCLUDED_FILE_SUFFIXES.some((suffix) => path.endsWith(suffix));
}

function walk(dir, results) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (isExcludedDir(path)) continue;
    const stats = statSync(path);
    if (stats.isDirectory()) {
      walk(path, results);
    } else if (SOURCE_EXTENSIONS.has(extname(path)) && !isExcludedFile(path)) {
      results.push(path);
    }
  }
  return results;
}

const files = walk(process.cwd(), []);
const violations = files
  .map((path) => ({ path, lines: readFileSync(path, "utf8").split("\n").length }))
  .filter((f) => f.lines > LIMIT);

if (violations.length > 0) {
  for (const v of violations) {
    console.error(`${v.path}: ${v.lines} lines (limit ${LIMIT})`);
  }
  console.error(`\n${violations.length} file(s) exceed the ${LIMIT}-line limit.`);
  process.exit(1);
}

console.log(`Checked ${files.length} source files. All within the ${LIMIT}-line limit.`);
