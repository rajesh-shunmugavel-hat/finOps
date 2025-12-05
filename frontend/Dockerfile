### Build stage
FROM node:20.19-alpine AS build
WORKDIR /app

# Install deps and build
COPY package.json package-lock.json* ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY public ./public
COPY src ./src
COPY tailwind.config.js ./
COPY postcss.config.js ./
# Install dependencies. npm ci is preferred for reproducible builds but can fail
# in some environments (lockfile mismatch, private registries). Try npm ci
# and if it fails, fall back to npm install with legacy peer deps and print
# npm debug info to help troubleshooting.
RUN set -eux; \
	npm ci --silent || (echo "npm ci failed, falling back to npm install" && npm install --legacy-peer-deps --no-audit --no-fund --silent); \
	npm --version; node --version; ls -la /app || true

RUN npm run build

### Production stage (nginx)
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
