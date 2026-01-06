/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

// Bundle analyzer for size comparison
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer(nextConfig);
