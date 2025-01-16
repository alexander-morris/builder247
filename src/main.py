import os
import sys
import cmd
import logging
import traceback
from pathlib import Path
import anthropic
import git

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

def clone_repository():
    """Clone the configured repository."""
    repo_url = os.getenv('REPO')
    if not repo_url:
        logger.error("REPO environment variable not set")
        return False
    
    # Convert HTTPS URL to SSH URL if needed
    if repo_url.startswith('https://github.com/'):
        repo_url = repo_url.replace('https://github.com/', 'git@github.com:')
        logger.info(f"Converted HTTPS URL to SSH URL: {repo_url}")
    
    repo_path = Path('/app/workspace/repo')
    if repo_path.exists():
        logger.info(f"Repository already exists at {repo_path}")
        try:
            repo = git.Repo(repo_path)
            # Set remote URL to SSH
            origin = repo.remote('origin')
            if origin.url != repo_url:
                origin.set_url(repo_url)
                logger.info(f"Updated remote URL to: {repo_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to update existing repository: {str(e)}")
            return False
    
    try:
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo_url, repo_path)
        logger.info(f"Repository cloned successfully to {repo_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to clone repository: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

class AgentCLI(cmd.Cmd):
    """Command line interface for the AI agent."""
    intro = 'Welcome to the AI Agent CLI. Type help or ? to list commands.\n'
    prompt = '(agent) '
    
    def __init__(self):
        super().__init__()
        self.client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229')
        self.conversation = []
    
    def do_chat(self, arg):
        """Send a message to Claude: chat <your message>"""
        if not arg:
            print("Please provide a message to send to Claude")
            return
            
        try:
            messages = self.conversation + [{
                "role": "user",
                "content": arg
            }]
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=messages
            )
            
            # Add the exchange to conversation history
            self.conversation.extend([
                {"role": "user", "content": arg},
                {"role": "assistant", "content": response.content[0].text}
            ])
            
            print("\nClaude:", response.content[0].text, "\n")
            
        except Exception as e:
            print(f"Error communicating with Claude: {str(e)}")
    
    def do_clear(self, arg):
        """Clear the conversation history"""
        self.conversation = []
        print("Conversation history cleared")
    
    def do_status(self, arg):
        """Check the agent's status"""
        print("\nAgent Status:")
        print("- Connected to Claude API")
        print(f"- Using model: {self.model}")
        print(f"- Conversation history: {len(self.conversation)//2} exchanges")
        print("- SSH keys configured")
        print(f"- Repository configured: {os.getenv('REPO')}")
        print(f"- Repository path: /app/workspace/repo\n")
    
    def do_exit(self, arg):
        """Exit the CLI"""
        print("Shutting down agent...")
        return True
    
    def do_EOF(self, arg):
        """Exit on EOF (Ctrl+D)"""
        print("\nShutting down agent...")
        return True

def check_environment_variables():
    """Verify required environment variables are present."""
    required_vars = ['SSH_KEY', 'SSH_KEY_PUB', 'CLAUDE_API_KEY', 'REPO']
    
    # Log all environment variables (excluding sensitive data)
    logger.info("Current environment variables:")
    for var in os.environ:
        if var in ['SSH_KEY', 'SSH_KEY_PUB', 'CLAUDE_API_KEY']:
            logger.info(f"- {var}: <redacted>")
        else:
            logger.info(f"- {var}: {os.getenv(var)}")
    
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        elif not value.strip():
            empty_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    if empty_vars:
        logger.error(f"Required environment variables are empty: {', '.join(empty_vars)}")
        return False
    
    logger.info("All required environment variables are present and non-empty")
    return True

def setup_ssh():
    """Configure SSH with provided keys."""
    ssh_dir = Path.home() / '.ssh'
    logger.info(f"Setting up SSH in directory: {ssh_dir}")
    
    try:
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        logger.info(f"Created SSH directory with permissions 700")
    except Exception as e:
        logger.error(f"Failed to create SSH directory: {e}")
        raise
    
    # Write private key
    private_key = os.getenv('SSH_KEY')
    if not private_key:
        raise ValueError("SSH_KEY is empty")
        
    try:
        # Replace \n with actual newlines
        private_key = private_key.replace('\\n', '\n')
        private_key_path = ssh_dir / 'id_rsa'
        private_key_path.write_text(private_key)
        private_key_path.chmod(0o600)
        logger.info("SSH private key written successfully with permissions 600")
    except Exception as e:
        logger.error(f"Failed to write private key: {e}")
        raise
    
    # Write public key
    public_key = os.getenv('SSH_KEY_PUB')
    if not public_key:
        raise ValueError("SSH_KEY_PUB is empty")
        
    try:
        public_key_path = ssh_dir / 'id_rsa.pub'
        public_key_path.write_text(public_key)
        public_key_path.chmod(0o644)
        logger.info("SSH public key written successfully with permissions 644")
    except Exception as e:
        logger.error(f"Failed to write public key: {e}")
        raise
        
    # Configure Git to use SSH
    try:
        os.system('git config --global core.sshCommand "ssh -i ~/.ssh/id_rsa -F /dev/null"')
        logger.info("Git configured to use SSH key")
    except Exception as e:
        logger.error(f"Failed to configure Git: {e}")
        raise

def test_claude_connectivity():
    """Test connection to Claude API."""
    try:
        logger.info("Testing Claude API connectivity...")
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            logger.error("CLAUDE_API_KEY is empty or not set")
            return False
            
        client = anthropic.Anthropic(api_key=api_key)
        logger.info("Created Anthropic client, attempting test message...")
        
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Say 'Connection successful' if you can read this."
            }]
        )
        
        response_text = message.content[0].text if message and message.content else "No response text"
        logger.info(f"Received response from Claude: {response_text}")
        
        if "Connection successful" in response_text:
            logger.info("Claude API connection test successful")
            return True
        else:
            logger.error(f"Claude API response was unexpected: {response_text}")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Claude API: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting environment verification")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Files in current directory: {os.listdir('.')}")
        
        if not check_environment_variables():
            logger.error("Environment verification failed")
            sys.exit(1)
        
        try:
            setup_ssh()
            logger.info("SSH setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup SSH: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)
        
        try:
            if not test_claude_connectivity():
                logger.error("Claude API setup failed")
                sys.exit(1)
            logger.info("Claude API setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup Claude API: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)
        
        try:
            if not clone_repository():
                logger.error("Repository setup failed")
                sys.exit(1)
            logger.info("Repository setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup repository: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)
        
        logger.info("Environment setup completed successfully")
        logger.info("Starting CLI interface...")
        
        # Start the CLI
        AgentCLI().cmdloop()
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main() 