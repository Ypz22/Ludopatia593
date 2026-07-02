FROM node:22-alpine AS build
WORKDIR /app
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
RUN addgroup -S app && adduser -S app -G app && chown -R app /app
USER app
EXPOSE 3000
CMD ["sh", "-c", "npm start -- -p ${PORT:-3000}"]
