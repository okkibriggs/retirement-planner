#!/bin/bash
export PORT=${PORT:-8080}
export STREAMLIT_SERVER_PORT=8501

envsubst '${PORT}' < /app/nginx.conf.template > /etc/nginx/nginx.conf

nginx -t 2>&1
streamlit run app.py --server.headless true &
sleep 2
nginx -g 'daemon off;'
