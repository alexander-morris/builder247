# AI Agent Container: Overview

This repository contains a Docker-based environment for an AI code-development agent. The agent can read and write files within the container, connect to a GitHub repository via SSH, and authenticate with the Claude API to perform iterative code generation and testing.

## Purpose

Provide an isolated, repeatable setup for local code development, testing, and secure file manipulation, minimizing outside intervention. By containerizing everything, you can quickly iterate on features while protecting sensitive data (SSH keys, API keys).

## Folder Structure

1. **Dockerfile**  
   Defines the container environment (Python, SSH, etc.) and exposes environment variables for the agent.  
2. **src/**  
   Contains Python scripts where the main logic resides, including the initial `main.py` that demonstrates reading environment variables.  
3. **tests/**  
   Holds test scripts that verify each core capability. For instance, checking environment variables, cloning a GitHub repo, and confirming file access.  
4. **docs/**  
   Contains markdown or readme files for a “happy path,” a to-do list of incremental tasks, and troubleshooting guides.

## How This Works

1. **Build and Run**  
   Build the Docker image, then run it with SSH keys and Claude API credentials passed in as environment variables.  
2. **Environment Variables**  
   The container references variables like `SSH_KEY`, `SSH_KEY_PUB`, and `CLAUDE_API_KEY`. They are used for GitHub repo access and calling Claude’s API.  
3. **Testing**  
   Each functionality (environment variables, Git cloning, file operations) has a corresponding test script in the `tests` directory.  
4. **Iterative Development**  
   Add or refine features, then run the tests to confirm everything works. Make small, incremental commits or branches to manage changes cleanly.

## Next Steps

1. **Follow the “Happy Path”**  
   Consult `docs/happy_path.md` (or a similarly named file) to see the recommended build and test flow.  
2. **Use the “To-Do” List**  
   Check `todo.readme` for upcoming tasks and features you can implement.  
3. **Troubleshoot When Needed**  
   Refer to `troubleshooting.readme` for permission errors, missing dependencies, or network issues.  
4. **Iterate and Commit**  
   Use separate branches for each feature. Commit when tests pass and the new feature meets the acceptance criteria.

That’s all you need to get started. By following this structure, an AI agent (or a human developer) can collaborate on code within a secure, containerized environment, smoothly iterating through features and tests.


# Repository Structure

1. **Root Directory**  
   - **Dockerfile**: Defines the container environment (Python, SSH tools, etc.).  
   - **README.md** (this file): Provides the high-level overview of the repository, purpose, and usage instructions.  

2. **src/**  
   - **main.py**: Starting point for the agent’s logic (e.g., reading environment variables, basic checks).  
   - *(Future files)*: Additional Python scripts containing agent capabilities, secure framework components, etc.

3. **tests/**  
   - **test_env_vars.py**: Verifies SSH and Claude environment variables are present.  
   - **test_git_clone.py**: Confirms the container can clone a public GitHub repo.  
   - *(Future files)*: Additional test scripts to check each incremental feature (e.g., private repo cloning, AI-driven file updates).

4. **docs/**  
   - **happy_path.md**: Outlines an ideal build–test flow for the container.  
   - **todo.md**: Lists incremental features and tasks.  
   - **troubleshooting.md**: Covers common issues (e.g., missing dependencies, permission errors).

These folders and files allow an AI agent, or a human developer, to build, test, and iterate on the project with minimal friction.# builder247
