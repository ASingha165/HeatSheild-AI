/**
 * Full-stack build script for HeatShield AI on Vercel.
 * Compiles the React/Vite frontend and populates root public/ and dist/ directories
 * for zero-config Vercel static asset serving alongside Python Serverless Functions.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');
const distDir = path.join(frontendDir, 'dist');
const publicDir = path.join(rootDir, 'public');
const rootDistDir = path.join(rootDir, 'dist');

console.log('[build_fullstack] Installing frontend dependencies...');
execSync('npm install', { cwd: frontendDir, stdio: 'inherit' });

console.log('[build_fullstack] Compiling frontend (tsc & vite build)...');
execSync('npm run build', { cwd: frontendDir, stdio: 'inherit' });

console.log('[build_fullstack] Copying compiled assets to root public/ directory...');
if (fs.existsSync(publicDir)) {
  fs.rmSync(publicDir, { recursive: true, force: true });
}
fs.mkdirSync(publicDir, { recursive: true });
fs.cpSync(distDir, publicDir, { recursive: true });

console.log('[build_fullstack] Copying compiled assets to root dist/ directory...');
if (fs.existsSync(rootDistDir)) {
  fs.rmSync(rootDistDir, { recursive: true, force: true });
}
fs.mkdirSync(rootDistDir, { recursive: true });
fs.cpSync(distDir, rootDistDir, { recursive: true });

console.log('[build_fullstack] Build successful! Assets ready in public/, dist/, and frontend/dist/.');
