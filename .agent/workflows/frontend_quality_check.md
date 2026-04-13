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

2.  **Run Formatter**
    - Run `npm run format` to automatically apply Prettier styling.
    ```bash
    npm run format
    ```

3.  **Run Linter**
    - Run `npm run lint` to check for Prettier and ESLint issues.
    - All errors must be resolved.
    ```bash
    npm run lint
    ```

4.  **Run Type and Diagnostic Checks**
    - Run `npm run check` for a complete Svelte and TypeScript validation.
    - Ensure 0 errors and 0 warnings.
    ```bash
    npm run check
    ```

5.  **Final Verification**
    - If any of the above commands fail (Exit Code != 0), you MUST fix the reported issues and re-run all three steps until they pass.
