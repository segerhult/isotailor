.
├── .github/          # CI/CD workflows
├── web/              # Frontend (Vue + Vite + Nginx)
│   ├── src/
│   │   ├── main.js
│   │   ├── api.js
│   │   └── App.vue
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ...
├── data/             # Runtime data (uploads, index)
├── server.py         # Backend Python HTTP server
├── Dockerfile        # Backend Docker image
├── docker-compose.yml
└── ...
