#!/bin/sh

# Replace environment variables in nginx configuration
envsubst '${BACKEND_URL}' < /etc/nginx/nginx.conf > /tmp/nginx.conf
mv /tmp/nginx.conf /etc/nginx/nginx.conf

# Replace environment variables in React build
if [ -n "$REACT_APP_API_URL" ]; then
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|REACT_APP_API_URL_PLACEHOLDER|$REACT_APP_API_URL|g" {} \;
fi

if [ -n "$REACT_APP_WS_URL" ]; then
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|REACT_APP_WS_URL_PLACEHOLDER|$REACT_APP_WS_URL|g" {} \;
fi

# Execute the main command
exec "$@"