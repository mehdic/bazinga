/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['better-sqlite3'],
  },
  webpack: (config) => {
    // Defensive check: ensure externals is an array before pushing
    if (!config.externals) {
      config.externals = [];
    } else if (!Array.isArray(config.externals)) {
      config.externals = [config.externals];
    }
    config.externals.push({
      'better-sqlite3': 'commonjs better-sqlite3',
    });
    return config;
  },
};

module.exports = nextConfig;
