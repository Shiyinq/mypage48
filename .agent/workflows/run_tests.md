---
description: Run the project's test suite, prioritizing the local virtual environment (.venv) if available.
---

This workflow guides the agent on how to correctly run tests, ensuring the isolated development environment is used when possible.

1.  **Check for Virtual Environment**
    - Check if a `.venv` directory exists in the project root.
    - You can use `ls -d .venv` or check the file structure.

2.  **Construct Test Command**
    - **Condition A**: If `.venv` exists:
      Use the Python executable within the virtual environment.
      Command: `.venv/bin/python -m pytest`
    
    - **Condition B**: If `.venv` does NOT exist:
      Use the system/global Python or Pytest.
      Command: `python -m pytest` or `pytest`

3.  **Execute Tests**
    - Append any specific test targets (e.g., `tests/`, `tests/test_health.py`) to the command.
    - Run the command.

    *Example (with .venv):*
    ```bash
    .venv/bin/python -m pytest tests/
    ```

    *Example (without .venv):*
    ```bash
    python -m pytest tests/
    ```
