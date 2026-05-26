/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: '/ide',
        destination: '/',
        permanent: true,
      },
      {
        source: '/ide/:path*',
        destination: '/',
        permanent: true,
      },
      {
        source: '/marketplace',
        destination: '/',
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
