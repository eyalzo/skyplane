# Skyplane Documentation

## Installation
Ensure that you are located within the project's root directory, and then execute the following command to install the necessary packages for documentation:

```bash
pip install -r docs/requirements.txt
```

## Running the server

To initiate the server, navigate to the project's root directory and execute the following command. This action will launch a server accessible at http://127.0.0.1:8000 (or a different available port if 8000 is already in use). Additionally, it will commence monitoring the `docs/` directory for any modifications.

Whenever a change is detected within the `docs/` directory, the documentation will be automatically regenerated, and any open browser windows will be refreshed. To halt the server, simply use the keyboard shortcut (Ctrl+C).

```bash
sphinx-autobuild -b html -d docs/build/doctrees docs docs/build/html
```

The anticipated result should resemble the following:

```
...
build succeeded.

The HTML pages are in docs/build/html.
[I 230825 10:29:28 server:335] Serving on http://127.0.0.1:8000
[I 230825 10:29:28 handlers:62] Start watching changes
[I 230825 10:29:28 handlers:64] Start detecting changes
```