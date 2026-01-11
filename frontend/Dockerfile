# ================================
# Stage 1: Build
# ================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_API_BASE_URL

# Set environment variables for build
ENV VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the application
RUN npm run build

# ================================
# Stage 2: Serve
# ================================
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
