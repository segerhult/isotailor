# Docker

## Overview
This repository includes Dockerfiles for building runnable images for the server and web components.

## Image Details

### Server Image

- Base image: `python:3.11-slim`

#### System Packages
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

### Web Image

Refer to the [Web Component Documentation](web/README.md) for details about the web image.

## Build

To build both the server and web images, use the following command:

NO_CHANGE