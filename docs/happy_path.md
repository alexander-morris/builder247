# Happy Path

This file provides a straightforward sequence of steps for building, testing, and iterating on the AI agent within the Docker container.

---

## Step 1: Build the Container
1. **Command**  
   ```bash
   docker build -t ai-agent:latest .
   ```
2. **Check**: Confirm that Python, SSH, and any required packages (like `git`) are installed as expected.

---

## Step 2: Run the Container with Environment Variables
1. **Command**  
   ```bash
   docker run -it \
     -e SSH_KEY="$(cat ~/.ssh/id_rsa)" \
     -e SSH_KEY_PUB="$(cat ~/.ssh/id_rsa.pub)" \
     -e CLAUDE_API_KEY="your-claude-key" \
     ai-agent:latest
   ```
2. **Check**: Ensure the container starts correctly and that the `main.py` script can read these variables.

---

## Step 3: Verify Environment Variables
1. **Command**  
   ```bash
   docker exec -it <container_name> python -m unittest tests/test_env_vars.py
   ```
2. **Check**: If all tests pass, the container can successfully read SSH and Claude API variables.

---

## Step 4: Clone a Public GitHub Repository
1. **Command**  
   ```bash
   docker exec -it <container_name> python -m unittest tests/test_git_clone.py
   ```
2. **Check**: The `test_git_clone.py` script should pass if it can clone a public repository. You can also verify by checking the container’s file system for the cloned directory.

---

## Step 5: (Optional) Set Up Private Repos
1. Update your Docker container or scripts to configure SSH properly (e.g., writing your private key to `~/.ssh/id_rsa`).
2. Clone a private repository. Verify it works by extending or adding a new test script (e.g., `test_git_clone_private.py`).

---

## Step 6: Iterate and Extend
- Add new features (e.g., modifying code in `src/`, writing additional tests).  
- Commit your changes in small, frequent increments.  
- Review logs and troubleshooting tips when encountering issues.

---

## Tips for the Agent
- **Keep Commits Small**: Make one feature change at a time, then run the tests.  
- **Use Branches**: Create a new branch for each enhancement or fix.  
- **Consult `troubleshooting.readme`**: For common errors (SSH issues, permission problems, etc.).  
- **Update `todo.readme`**: Keep track of upcoming tasks and mark them complete as you go.

By following these steps, you can reliably build, test, and enhance the AI agent environment.