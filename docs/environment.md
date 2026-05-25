# Environment

## Runtime

This section details the environment variables and configuration required to run and test this repository.

-   **Python Version:** 3.11 (as specified in the `Dockerfile`)

For details on how to run the application using Docker, see the [Docker Setup](#docker-setup) section.

## CI/CD

This section documents secrets and environment variables required by the CI pipelines defined in `.github/workflows/main.yml`. Currently, the CI pipeline uses GitHub Actions.

## Docker Setup

The project utilizes Docker and Docker Compose for local development and testing.

1.  **Install Docker:** Ensure Docker and Docker Compose are installed on your system.  Refer to the official Docker documentation for installation instructions: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

2.  **Build the application:** Navigate to the root directory of the repository and run `docker-compose up --build`. This command builds the necessary images based on the `Dockerfile` and `web/Dockerfile` and starts the containers defined in `docker-compose.yml`.

3.  **Access the application:** Once the containers are running, access the application in your browser at `http://localhost:80`.

**Docker Configuration Files:**

-   `Dockerfile`: Defines the build process for the Python backend.
-   `docker-compose.yml`: Defines the services and their configurations for the application stack.
-   `.dockerignore`: Specifies files and directories to exclude from the Docker image build context.
-   `web/Dockerfile`: Defines the build process for the Vue.js frontend.
-   `web/.dockerignore`: Specifies files and directories to exclude from the Vue.js Docker image build context.

## AI (Optional)

This repository does not currently utilize any AI tooling in its CI/CD pipelines.
