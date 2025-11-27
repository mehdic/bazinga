/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for self-contained deployment
  // This creates a minimal server that doesn't require node_modules
  output: 'standalone',

  // serverComponentsExternalPackages handles native modules in Next.js 14+
  // No additional webpack config needed for better-sqlite3
  experimental: {
    serverComponentsExternalPackages: ['better-sqlite3'],
  },
};

module.exports = nextConfig;
