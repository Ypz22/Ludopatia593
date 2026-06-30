/** @type {import('next').NextConfig} */
// El navegador llama al backend directo (lib/api.ts usa NEXT_PUBLIC_API_URL).
// Sin rewrites: Next los congela en build y rompían el destino en Docker.
module.exports = {};
