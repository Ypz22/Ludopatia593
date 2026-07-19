FROM node:22-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
# Cuentas demo en el login: solo se muestran si vale "1" (local/compose). En un
# despliegue real no se define -> el bloque no se compila en el bundle.
ARG NEXT_PUBLIC_DEMO_ACCOUNTS=0
ENV NEXT_PUBLIC_DEMO_ACCOUNTS=${NEXT_PUBLIC_DEMO_ACCOUNTS}
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
# El runtime NO usa el CLI de npm (arrancamos `next` directo). Se elimina el npm
# bundleado en la imagen base para no arrastrar sus vulnerabilidades (picomatch,
# sigstore) que Trivy detecta en /usr/local/lib/node_modules/npm -- no son deps
# de la app, sino del CLI que no se ejecuta en producción.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx
RUN addgroup -S app && adduser -S app -G app && chown -R app /app
USER app
EXPOSE 3000
CMD ["sh", "-c", "node_modules/.bin/next start -p ${PORT:-3000}"]
