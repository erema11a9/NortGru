# Stage 1: Build the Vue application
FROM node:18-alpine AS build-stage

WORKDIR /app

# Copy package configurations and install dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy application source files
COPY . .

# Build the app for production
ENV NODE_OPTIONS="--max-old-space-size=1024"
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:1.25-alpine

# Copy Nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts to Nginx html directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
