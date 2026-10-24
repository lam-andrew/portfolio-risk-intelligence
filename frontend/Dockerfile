# Orbit frontend — React + TypeScript
#
# Targets (ADR 0028):
#   production  — the compiled app served by Caddy, which also proxies /api to the API on the
#                 same origin; used by docker-compose.prod.yml.
#   development — the default (last) target: the Vite dev server; used by CI and local Compose.
FROM node:20-slim AS deps

WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json package-lock.json* ./
RUN npm install


FROM deps AS build

COPY . .
# Same-origin API: the proxy serves /api, so no host is baked into the bundle.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM caddy:2.11.7-alpine AS production

# Caddy needs no root: it listens on an unprivileged port with TLS and the admin API off.
RUN addgroup -S web && adduser -S -G web web
ENV XDG_CONFIG_HOME=/tmp/caddy-config \
    XDG_DATA_HOME=/tmp/caddy-data
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
USER web

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]


FROM deps AS development

COPY . .

# The node image ships a non-root `node` user; run as it (Trivy DS-0002).
RUN chown -R node:node /app
USER node

EXPOSE 5173

# Report container health by fetching the dev server's index (Trivy DS-0026).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://localhost:5173').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Dev server bound to all interfaces (see vite.config.ts) so the host can reach it.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
