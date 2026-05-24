# Docker

## Overview
This repository includes Dockerfiles for both the server and web components, as well as a `docker-compose.yml` file to manage them together.

## Server Image Details (Dockerfile)
- Base image: `python:3.11-slim`

### System Packages
- `curl`
- `git`
- `htop`
- `nano`
- `openssh-server`
- `python3`
- `rsync`
- `sudo`
- `vim`
- `wget`

## Web Image Details (web/Dockerfile)
This image is built using Vite. See `web/vite.config.js` for build configuration details.

## Build
To build the server image, navigate to the root directory of the repository and run: