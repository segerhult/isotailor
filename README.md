# isotailor
Easy iso image tailor tool

isotailor is a tool that allows users to upload ISO images and select software to be included in the tailored ISO. The software can be chosen from a default list or provided as custom entries.

## Usage
1.  Navigate to the root directory of the isotailor repository.
2.  Run the server using `python server.py`.
3.  Access the isotailor web interface in your browser at `http://localhost:8000`.

## Features

*   **ISO Upload:** Upload ISO files to be tailored.
*   **Software Selection:** Choose from a predefined list of software packages or enter custom packages.
*   **Existing Uploads:** View and manage previously uploaded ISOs.

## Data Storage

Data, including uploaded ISOs and configuration, is stored locally in the `./data` directory. It’s recommended to back up this directory to prevent loss of data.

## API
For developers, the isotailor API is available at `/api`. The API documentation is available in the [doc/openapi.md](doc/openapi.md) file.