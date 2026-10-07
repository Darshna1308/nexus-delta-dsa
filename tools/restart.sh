#!/bin/bash
for p in $(ps -eo pid,args | awk '/[s]treamlit/ && !/restart/ {print $1}'); do kill $p 2>/dev/null; done
sleep 1
cd "$(dirname "$0")/.."
nohup python3 -m streamlit run app.py --server.port 8765 --server.headless true > /tmp/st.log 2>&1 &
sleep 7
curl -s -o /dev/null -w "%{http_code}\n" localhost:8765
