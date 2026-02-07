#!/bin/bash
envsubst '${PORT}' < /app/nginx.conf.template > /etc/nginx/conf.d/default.conf
streamlit run app.py --server.port 8501 --server.headless true &
nginx -g 'daemon off;'
