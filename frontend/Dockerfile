# Stage 1: Build
FROM node:20.10.0-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage layer caching
COPY package*.json ./

# Install dependencies using npm ci and cache mounts for speed
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy the rest of the application code
COPY . .

# Define build arguments
ARG PUBLIC_CLIENT_SIDE_API_BASE_URL
ARG PUBLIC_SERVER_SIDE_API_BASE_URL
ARG PUBLIC_UMAMI_WEBSITE_ID
ARG PUBLIC_UMAMI_URL

# Set environment variables for the build
ENV PUBLIC_CLIENT_SIDE_API_BASE_URL=$PUBLIC_CLIENT_SIDE_API_BASE_URL
ENV PUBLIC_SERVER_SIDE_API_BASE_URL=$PUBLIC_SERVER_SIDE_API_BASE_URL
ENV PUBLIC_UMAMI_WEBSITE_ID=$PUBLIC_UMAMI_WEBSITE_ID
ENV PUBLIC_UMAMI_URL=$PUBLIC_UMAMI_URL

# Build the Svelte application
RUN npm run build

# Stage 2: Runtime
FROM node:20.10.0-alpine AS runtime

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json

# Install only production dependencies
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev

# Expose port 5050
EXPOSE 5050

# Command to run the app
CMD ["node", "build/index.js"]
