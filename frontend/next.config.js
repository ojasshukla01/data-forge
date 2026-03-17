const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: __dirname,
  },
  async rewrites() {
    const apiOrigin =
      process.env.DATA_FORGE_API_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // OneDrive paths + stray package.json in home dir confuse resolution.
    // Force resolution context to frontend/ so tailwindcss is found.
    config.context = __dirname;
    config.resolve.modules = [
      path.join(__dirname, 'node_modules'),
      ...(config.resolve.modules || []),
    ];
    config.resolve.alias = {
      ...config.resolve.alias,
      tailwindcss: path.join(__dirname, 'node_modules', 'tailwindcss'),
      '@tailwindcss/postcss': path.join(__dirname, 'node_modules', '@tailwindcss/postcss'),
    };
    return config;
  },
};

module.exports = nextConfig;
