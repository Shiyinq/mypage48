# Use an official node image with Node.js version 20.10.0
FROM node:20.10.0-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Define build arguments
ARG PUBLIC_CLIENT_SIDE_API_BASE_URL
ARG PUBLIC_SERVER_SIDE_API_BASE_URL

# Set environment variables using the build arguments
ENV PUBLIC_CLIENT_SIDE_API_BASE_URL=$PUBLIC_CLIENT_SIDE_API_BASE_URL
ENV PUBLIC_SERVER_SIDE_API_BASE_URL=$PUBLIC_SERVER_SIDE_API_BASE_URL

# Build the Svelte application
RUN npm run build

# Expose port 5050
EXPOSE 5050

# Command to run the app
CMD ["node","build/index.js"]
