/** @type {import('next').NextConfig} */
// El navegador llama al backend directo (lib/api.ts usa NEXT_PUBLIC_API_URL).
// Sin rewrites: Next los congela en build y rompían el destino en Docker.
// poweredByHeader:false -> no revelar 'X-Powered-By: Next.js' (menos recon).
module.exports = { poweredByHeader: false };
