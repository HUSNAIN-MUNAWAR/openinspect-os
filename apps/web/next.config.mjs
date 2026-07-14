/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  outputFileTracingRoot: process.cwd(),
  experimental: { cpus: 1, webpackBuildWorker: false, parallelServerBuildTraces: false, parallelServerCompiles: false },
};
export default nextConfig;
