---
description: Ensure the frontend code meets quality standards (formatter, lint, type-check) before finalizing updates or new features.
---

This workflow ensures that frontend changes are stable, well-formatted, and free of linting or TypeScript errors. Run this before completing any frontend task.

1.  **Initialize Environment (NVM)**
    - If `npm` is not recognized or fails, initialize NVM first to ensure the correct Node.js version is used.
    ```bash
    source ~/.nvm/nvm.sh && nvm use default
    ```

2.  **Navigate to Frontend Directory**
    - The frontend project is located in the `frontend` directory.
    - `cd frontend` (instructional, the agent handles the Cwd).

3.  **Run All Quality Checks (Highly Recommended)**
    - To guarantee absolute correctness and prevent any errors from being overlooked (which can happen when run individually), execute all checks in a single combined command:
    ```bash
    npm run check && npm run format && npm run lint
    ```
    - If the combined command passes with exit code 0, the verification is complete and fully successful!

4.  **Individual Check Commands (Alternative / Debugging)**
    - If the combined command fails, or if you need to run/debug steps individually, you can use the following commands:
    
    - **A. Formatter** (Apply Prettier styling):
      ```bash
      npm run format
      ```
    
    - **B. Linter** (Check ESLint and Prettier issues):
      ```bash
      npm run lint
      ```
    
    - **C. Type and Diagnostic Checks** (Complete Svelte and TypeScript validation):
      ```bash
      npm run check
      ```

5.  **Final Verification**
    - If any check fails, you MUST fix the reported issues and re-run the verification (preferably the combined command in Step 3) until it completely passes.
