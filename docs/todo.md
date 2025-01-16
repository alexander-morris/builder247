```markdown
# todo.readme

## Planned Tasks with Acceptance Criteria

1. **SSH Key Integration**  
   - **Task**: Store private/public SSH keys securely in the container (e.g., via environment variables). Write a script to configure `~/.ssh` and confirm that private repos can be cloned.  
   - **Acceptance**: We can run a test that successfully clones a private repo without prompting for credentials. The container logs should show no errors related to SSH setup.

2. **Claude API Integration**  
   - **Task**: Extend `main.py` to authenticate with Claude using the `CLAUDE_API_KEY`. Write a basic script that makes a request to Claude’s API to confirm connectivity.  
   - **Acceptance**: A simple call to Claude’s API returns a valid response, and the logs confirm the request and response without any authentication errors.

3. **File Manipulation & Logging**  
   - **Task**: Enable the agent to read, modify, and create files in the container. Develop logging for every change (file edits, test runs, etc.) to support future reviews.  
   - **Acceptance**: A test script that creates, modifies, and deletes a file runs without error. The logs clearly indicate each operation (timestamp + action details).

4. **Automated Testing**  
   - **Task**: Create or extend test files to cover each new feature (SSH configuration, API calls, file operations). Maintain a quick feedback loop for errors.  
   - **Acceptance**: All tests can be run with a single command (e.g., `python -m unittest discover tests`) and pass without failures. CI or local logs confirm test results clearly.

5. **Security Hardening**  
   - **Task**: Evaluate permissions for the container’s user. Restrict access or add firewalls/whitelists if needed.  
   - **Acceptance**: Any privileged actions are restricted to authorized users only. Attempting to perform out-of-scope actions (e.g., accessing system files) fails with a permission error. Logs clearly reflect any security-related events.

6. **Extended Capabilities**  
   - **Task**: Add more complex AI-driven tasks (e.g., proposing code changes, running code analysis). Optionally integrate with additional frameworks or libraries.  
   - **Acceptance**: The new AI tasks can be triggered from `main.py` or a new script. A test script or manual check verifies the AI system can handle these tasks without errors, logging all file changes and outputs.

7. **Workflow / CI Integration**  
   - **Task**: Configure a CI pipeline that automatically builds the Docker image and runs tests. Ensure new commits trigger these checks and require successful tests before merging.  
   - **Acceptance**: Opening a PR or pushing a commit triggers a CI run that builds the Docker image and executes tests. Changes are only mergeable when all tests pass.

---

Tackle each item in a separate branch. After completing a task, confirm it meets the acceptance criteria, commit, and merge. Then move on to the next item. Keep this list updated as new needs arise.
```