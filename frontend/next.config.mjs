/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Produces a self-contained server bundle (.next/standalone) used by the
  // Docker image so it does not need node_modules at runtime.
  output: "standalone",
};

export default nextConfig;
