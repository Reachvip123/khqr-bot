# syntax = docker/dockerfile:1

# Adjust BUN_VERSION as desired
ARG BUN_VERSION=1.2.20
FROM oven/bun:${BUN_VERSION}-slim AS base

# Bun app lives here
WORKDIR /app

# Set production environment
ENV NODE_ENV="production"

# Throw-away build stage to reduce size of final image
FROM base AS build

# Install node modules
COPY bun.lock package.json ./
RUN bun install --ci

# Copy application code
COPY . .

# Final stage for app image
FROM base

ARG PORT=3000
ENV PORT=${PORT}

# Copy built application
COPY --from=build /app /app

# Start the server by default; this can be overwritten at runtime
EXPOSE ${PORT}
CMD [ "bun", "start" ]
