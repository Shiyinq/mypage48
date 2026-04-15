---
description: Run the project's test suite, prioritizing the local virtual environment (.venv) if available.
---

This workflow guides the agent on how to correctly run tests, ensuring the isolated development environment is used when possible.

1.  **Initialize Environment (.venv)**
    - Always prioritize using the local virtual environment for consistent dependencies.
    - If you are running tasks in a shell session, activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

2.  **Construct and Execute Test Command**
    - **Method A (Direct Path)**: If you prefer not to activate the shell, use the full path to the python executable:
      Command: `.venv/bin/python -m pytest`
    
    - **Method B (Activated Shell)**: If `.venv` is already activated:
      Command: `python -m pytest`
    
3.  **Execute Tests**
    - Append any specific test targets to the command to run specific suites or files.
    - Common targets: `tests/`, `tests/test_auth.py`, `tests/test_health.py`, `tests/test_users.py`.

    *Example (Specific file):*
    ```bash
    .venv/bin/python -m pytest tests/test_auth.py
    ```

    *Example (Entire suite):*
    ```bash
    .venv/bin/python -m pytest tests/
    ```
