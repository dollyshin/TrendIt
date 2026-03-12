/** @type {import('next').NextConfig} */
const apiUrl = process.env.API_URL || 'http://localhost:8000'
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${apiUrl}/:path*` }]
  },
}

module.exports = nextConfig
