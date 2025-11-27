/** @type {import('next').NextConfig} */
const nextConfig = {
  // serverComponentsExternalPackages handles native modules in Next.js 14+
  // No additional webpack config needed for better-sqlite3
  experimental: {
    serverComponentsExternalPackages: ['better-sqlite3'],
  },
};

module.exports = nextConfig;
