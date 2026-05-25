# Docker

## Overview
This repository includes a `Dockerfile` and a `docker-compose.yml` file for containerization. The `web` subdirectory also contains a `Dockerfile` for the frontend.

## Server Image Details
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

## Build

To build the server image: