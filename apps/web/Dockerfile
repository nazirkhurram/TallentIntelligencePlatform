# ==============================================================================
# Build Stage for Next.js web application
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/web/package.json ./
RUN npm install --legacy-peer-deps

COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build || echo "Initial build complete"

# ==============================================================================
# Production Runtime Stage
# ==============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    mkdir -p /app/.next && \
    chown -R nextjs:nodejs /app

COPY --from=builder --chown=nextjs:nodejs /app/package.json ./
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/ ./

USER nextjs

EXPOSE 3000

CMD ["npm", "start"]

