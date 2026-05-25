.
├── server.py          # Python backend HTTP server
├── Dockerfile         # Backend container definition
├── docker-compose.yml # Multi-service container orchestration
├── web/               # Frontend Vue + Vite project
│   ├── src/
│   │   ├── main.js    # Vue entry point
│   │   ├── App.vue    # Root component
│   │   └── api.js     # API client (Axios-like abstraction over fetch)
│   ├── nginx.conf     # Nginx static file config
│   ├── Dockerfile     # Frontend container (Nginx)
│   └── ...
├── data/              # Runtime storage (created at runtime)
│   ├── uploads/       # Uploaded files
│   └── uploads.json   # Index of uploaded files
└── .github/           # CI/CD workflows
