# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time env vars (NEXT_PUBLIC_* must be present at build time)
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_COGNITO_REGION
ARG NEXT_PUBLIC_COGNITO_USER_POOL_ID
ARG NEXT_PUBLIC_COGNITO_APP_CLIENT_ID

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_COGNITO_REGION=$NEXT_PUBLIC_COGNITO_REGION
ENV NEXT_PUBLIC_COGNITO_USER_POOL_ID=$NEXT_PUBLIC_COGNITO_USER_POOL_ID
ENV NEXT_PUBLIC_COGNITO_APP_CLIENT_ID=$NEXT_PUBLIC_COGNITO_APP_CLIENT_ID

RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only what's needed for production
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
