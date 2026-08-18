FROM node:24-bookworm-slim AS dependencies

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM dependencies AS builder
COPY . .
RUN pnpm build

FROM dependencies AS production-dependencies
RUN pnpm prune --prod

FROM node:24-bookworm-slim AS runtime

ENV NODE_ENV=production
ENV API_BASE_URL=http://backend:8000
WORKDIR /app

COPY --from=production-dependencies /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/.next ./.next

EXPOSE 3000

CMD ["./node_modules/.bin/next", "start"]
