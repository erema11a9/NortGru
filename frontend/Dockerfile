# Serve using Nginx
FROM nginx:1.25-alpine

# Copy Nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy prebuilt local build artifacts to Nginx html directory
COPY dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
