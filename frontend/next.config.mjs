/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy all /api requests to the FastAPI backend.
  // In Docker Compose, 'web' is the service name for the FastAPI container.
  // NEXT_PUBLIC_API_URL can be set to override at build time for different environments.
  async rewrites() {
    const apiBase = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://web:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
