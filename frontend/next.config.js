/** @type {import('next').NextConfig} */
// BACKEND_URL es server-only (sin prefijo NEXT_PUBLIC_) -> Next NO lo hornea en
// build; se lee en runtime al iniciar `next start`. En Docker apunta al servicio
// backend; en dev local cae a localhost:8000.
const API = process.env.BACKEND_URL || "http://localhost:8000";
module.exports = {
  async rewrites() {
    // proxy /api/* -> backend (evita CORS y oculta el origen real al navegador)
    return [{ source: "/api/:path*", destination: `${API}/:path*` }];
  },
};
