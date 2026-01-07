# Frontend Dockerfile for NotebookLM Next.js App
# Multi-stage build with nginx for static serving

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Accept build arguments for environment variables FIRST (before COPY)
# ARG values must be declared before they're used in ENV
ARG NEXT_PUBLIC_API_URL
ARG NODE_ENV=production

# Set environment variables for build
# NEXT_PUBLIC_* variables must be available at build time for Next.js static generation
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=${NODE_ENV}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build the application (static export)
RUN npm run build

# Stage 3: Nginx Runner
FROM nginx:alpine AS runner

# Copy nginx configuration (from build context, not builder stage)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static export output to nginx html directory
COPY --from=builder /app/out /usr/share/nginx/html

# Expose port 3019 (can be overridden via PORT env var, but nginx.conf uses 3019)
EXPOSE 3019

# Set port environment variable (defaults to 3019)
# Note: nginx.conf is hardcoded to 3019, but we keep PORT for consistency
ENV PORT=3019

# Health check - checks nginx on port 3019
# Install wget for health check (nginx:alpine doesn't include it by default)
RUN apk add --no-cache wget
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3019 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
