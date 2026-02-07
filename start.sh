#!/bin/bash
export PORT=${PORT:-8080}
export STREAMLIT_SERVER_PORT=8501

envsubst '${PORT}' < /app/nginx.conf.template > /etc/nginx/conf.d/app.conf
rm -f /etc/nginx/sites-enabled/default

nginx -t && echo "nginx config OK" || echo "nginx config FAILED"

streamlit run app.py --server.headless true &
sleep 2
nginx -g 'daemon off;'
