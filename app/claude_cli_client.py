"""Claude CLI client for the Self-Evolving Web Application.

This module provides a client for interacting with Claude CLI with structured prompts,
workflow-specific templates, and response parsing and validation.

The Claude CLI integration provides analysis through explicit context provided in prompts,
enabling Claude to understand the application architecture and provide accurate suggestions
without requiring repository access tokens.
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaudeCLIError(Exception):
    """Custom exception for Claude CLI errors."""
    pass


class ClaudeResponseValidationError(ClaudeCLIError):
    """Raised when Claude response doesn't meet validation requirements."""
    pass


@dataclass
class ClaudeCLIResponse:
    """Structured response from Claude CLI."""
    content: str
    model: str
    timestamp: datetime
    repository_context: bool
    command_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "repository_context": self.repository_context,
            "command_used": self.command_used
        }


class ClaudeCLIClient:
    """
    Claude CLI client with structured prompts and constrained response handling.
    
    Provides methods for workflow-specific Claude interactions with explicit context
    provided through prompts, enabling accurate analysis without repository access tokens.
    """
    
    def __init__(
        self, 
        repository_root: Optional[str] = None,
        claude_command: str = "claude",
        timeout: int = 300,
        model: str = "sonnet"  # Use alias instead of full model name
    ):
        """
        Initialize Claude CLI client.
        
        Args:
            repository_root: Path to repository root (defaults to current directory)
            claude_command: Claude CLI command name
            timeout: Command timeout in seconds
            model: Claude model to use
        """
        self.repository_root = Path(repository_root or os.getcwd()).resolve()
        self.claude_command = claude_command
        self.timeout = timeout
        self.model = model
        
        # Verify Claude CLI is available
        self._verify_claude_cli()
        
        # Verify repository context
        self._verify_repository_context()
    
    def _verify_claude_cli(self) -> None:
        """Verify Claude CLI is installed and accessible."""
        try:
            result = subprocess.run(
                [self.claude_command, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise ClaudeCLIError(f"Claude CLI not working: {result.stderr}")
            
            logger.info(f"Claude CLI verified: {result.stdout.strip()}")
            
        except subprocess.TimeoutExpired:
            raise ClaudeCLIError("Claude CLI verification timed out")
        except FileNotFoundError:
            raise ClaudeCLIError(
                f"Claude CLI command '{self.claude_command}' not found. "
                "Please install Claude CLI: https://docs.anthropic.com/claude/docs/cli"
            )
        except Exception as e:
            raise ClaudeCLIError(f"Failed to verify Claude CLI: {str(e)}")
    
    def _verify_repository_context(self) -> None:
        """Verify repository root exists for context information (not used for Claude CLI access)."""
        if not self.repository_root.exists():
            logger.warning(f"Repository root does not exist: {self.repository_root}")
        else:
            logger.info(f"Repository root found: {self.repository_root} (used for context only)")
    
    def _get_session_token(self) -> Optional[str]:
        """
        Get Claude session token from environment or keychain.
        
        Returns:
            Session token if available, None otherwise
        """
        # First try environment variable
        token = os.getenv('CLAUDE_CODE_SESSION_ACCESS_TOKEN')
        if token:
            return token
        
        # Try to get from macOS keychain (for local development)
        try:
            result = subprocess.run([
                'security', 'find-generic-password', 
                '-s', 'Claude Code-credentials', 
                '-w'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                credentials = json.loads(result.stdout.strip())
                return credentials.get('claudeAiOauth', {}).get('accessToken')
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, Exception):
            # Keychain access failed, continue without token
            pass
        
        return None

    def _execute_claude_command(
        self,
        prompt: str,
        additional_args: Optional[List[str]] = None,
        working_directory: Optional[str] = None
    ) -> ClaudeCLIResponse:
        """
        Execute Claude CLI command with repository context.
        
        Args:
            prompt: Prompt to send to Claude
            additional_args: Additional CLI arguments
            working_directory: Working directory for command execution
            
        Returns:
            ClaudeCLIResponse with content and metadata
            
        Raises:
            ClaudeCLIError: If command execution fails
        """
        try:
            # Prepare command arguments - use --print for non-interactive mode
            cmd_args = [self.claude_command, "--print"]
            
            # Add model specification if supported
            if self.model:
                cmd_args.extend(["--model", self.model])
            
            # Add additional arguments
            if additional_args:
                cmd_args.extend(additional_args)
            
            # Use repository root as working directory for context
            work_dir = str(self.repository_root)
            
            # Prepare environment with session token
            env = os.environ.copy()
            session_token = self._get_session_token()
            if session_token:
                env['CLAUDE_CODE_SESSION_ACCESS_TOKEN'] = session_token
            
            # DETAILED LOGGING
            print(f"🔍 CLAUDE CLI DEBUG:")
            print(f"   Command: {' '.join(cmd_args)}")
            print(f"   Working Directory: {work_dir}")
            print(f"   Repository Root: {self.repository_root}")
            print(f"   Session Token: {'✅ Available' if session_token else '❌ Not Found'}")
            print(f"   Environment Variables:")
            for key in ['CLAUDE_CODE_SESSION_ACCESS_TOKEN', 'REPO_ROOT', 'PYTHONPATH']:
                value = env.get(key, 'NOT SET')
                if 'TOKEN' in key and value != 'NOT SET':
                    print(f"     {key}: {value[:10]}...{value[-4:] if len(value) > 4 else '***'}")
                else:
                    print(f"     {key}: {value}")
            print(f"   Prompt length: {len(prompt)} characters")
            
            # Create temporary file for prompt if it's long
            if len(prompt) > 1000:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(prompt)
                    temp_file = f.name
                
                try:
                    # Use file input for long prompts
                    cmd_args.extend(["--file", temp_file])
                    
                    # Execute command
                    result = subprocess.run(
                        cmd_args,
                        cwd=work_dir,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file)
            else:
                # Use direct prompt for short prompts
                cmd_args.append(prompt)
                
                # Execute command
                result = subprocess.run(
                    cmd_args,
                    cwd=work_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            
            # DETAILED OUTPUT LOGGING
            print(f"🔍 CLAUDE CLI RESULT:")
            print(f"   Return Code: {result.returncode}")
            print(f"   STDOUT: {result.stdout[:200]}{'...' if len(result.stdout) > 200 else ''}")
            print(f"   STDERR: {result.stderr[:200]}{'...' if len(result.stderr) > 200 else ''}")
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                
                # Special handling for session token errors
                if "session token" in error_msg.lower() or "CLAUDE_CODE_SESSION_ACCESS_TOKEN" in error_msg:
                    if not session_token:
                        raise ClaudeCLIError(
                            "Claude CLI requires session token for repository context. "
                            "Please set CLAUDE_CODE_SESSION_ACCESS_TOKEN environment variable "
                            "or ensure Claude CLI is properly authenticated."
                        )
                    else:
                        raise ClaudeCLIError(f"Claude CLI session token error: {error_msg}")
                
                raise ClaudeCLIError(f"Claude CLI command failed (exit code {result.returncode}): {error_msg}")
            
            # Parse response
            content = result.stdout.strip()
            if not content:
                raise ClaudeCLIError("Claude CLI returned empty response")
            
            return ClaudeCLIResponse(
                content=content,
                model=self.model,
                timestamp=datetime.utcnow(),
                repository_context=True,  # Now using repository context
                command_used=" ".join(cmd_args[:3])  # First 3 args for logging
            )
            
        except subprocess.TimeoutExpired:
            raise ClaudeCLIError(f"Claude CLI command timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e, ClaudeCLIError):
                raise
            raise ClaudeCLIError(f"Failed to execute Claude CLI command: {str(e)}")
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> ClaudeCLIResponse:
        """
        Generate response from Claude CLI with repository context.
        
        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional system prompt for context
            additional_context: Additional context to include
            
        Returns:
            ClaudeCLIResponse with content and metadata
            
        Raises:
            ClaudeCLIError: If command execution fails
        """
        try:
            # Construct full prompt with context
            full_prompt_parts = []
            
            if system_prompt:
                full_prompt_parts.append(f"SYSTEM: {system_prompt}")
                full_prompt_parts.append("")
            
            if additional_context:
                full_prompt_parts.append(f"CONTEXT: {additional_context}")
                full_prompt_parts.append("")
            
            full_prompt_parts.append(f"USER: {prompt}")
            
            full_prompt = "\n".join(full_prompt_parts)
            
            # Execute Claude CLI command
            return self._execute_claude_command(full_prompt)
            
        except Exception as e:
            if isinstance(e, ClaudeCLIError):
                raise
            raise ClaudeCLIError(f"Failed to generate response: {str(e)}")
    
    def triage_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform triage analysis using Claude CLI with repository context.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed triage analysis with structured fields
            
        Raises:
            ClaudeCLIError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting repository-aware triage analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a technical triage analyst with full access to the repository context. "
                "Analyze the provided issue using your understanding of the codebase structure, "
                "existing patterns, and architectural decisions. Respond in the exact format "
                "requested. Be concise but thorough. Focus only on understanding the problem, "
                "not on implementation."
            )
            
            additional_context = (
                f"Repository: {self.repository_root}\n"
                f"Trace ID: {trace_id}\n"
                "You have access to all files in this repository for context."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                system_prompt=system_prompt,
                additional_context=additional_context
            )
            
            # Parse and validate triage response
            parsed_response = self._parse_triage_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "triage",
                "repository_context": response.repository_context,
                "command_used": response.command_used
            }
            
            logger.info(f"Completed repository-aware triage analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeCLIError:
            raise
        except Exception as e:
            raise ClaudeCLIError(f"Triage analysis failed for trace_id {trace_id}: {str(e)}")
    
    def planning_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform planning analysis using Claude CLI with repository context.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed planning analysis with structured fields
            
        Raises:
            ClaudeCLIError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting repository-aware planning analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a technical architect with full access to the repository context. "
                "Create detailed implementation plans by understanding the existing codebase "
                "structure, patterns, and dependencies. Reference specific files and functions "
                "where appropriate. Focus on approach, design, and testing strategy without "
                "writing actual code. Respond in the exact format requested."
            )
            
            additional_context = (
                f"Repository: {self.repository_root}\n"
                f"Trace ID: {trace_id}\n"
                "You can reference any file in the repository and understand the full "
                "codebase architecture for your planning."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                system_prompt=system_prompt,
                additional_context=additional_context
            )
            
            # Parse and validate planning response
            parsed_response = self._parse_planning_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "planning",
                "repository_context": response.repository_context,
                "command_used": response.command_used
            }
            
            logger.info(f"Completed repository-aware planning analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeCLIError:
            raise
        except Exception as e:
            raise ClaudeCLIError(f"Planning analysis failed for trace_id {trace_id}: {str(e)}")
    
    def prioritization_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform prioritization analysis using Claude CLI with repository context.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed prioritization analysis with structured fields
            
        Raises:
            ClaudeCLIError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting repository-aware prioritization analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a product manager with full access to the repository context. "
                "Assess priorities by understanding the codebase complexity, existing "
                "technical debt, and architectural implications. Evaluate user value, "
                "effort, and risk with deep understanding of the implementation context. "
                "Do not make implementation decisions. Respond in the exact format requested."
            )
            
            additional_context = (
                f"Repository: {self.repository_root}\n"
                f"Trace ID: {trace_id}\n"
                "You can analyze the codebase to understand implementation complexity "
                "and architectural impact for accurate prioritization."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                system_prompt=system_prompt,
                additional_context=additional_context
            )
            
            # Parse and validate prioritization response
            parsed_response = self._parse_prioritization_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "prioritization",
                "repository_context": response.repository_context,
                "command_used": response.command_used
            }
            
            logger.info(f"Completed repository-aware prioritization analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeCLIError:
            raise
        except Exception as e:
            raise ClaudeCLIError(f"Prioritization analysis failed for trace_id {trace_id}: {str(e)}")
    
    def implementation_generation(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Generate implementation using Claude CLI with repository context.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed implementation with code and tests
            
        Raises:
            ClaudeCLIError: If generation fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting repository-aware implementation generation for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a senior software engineer with full access to the repository context. "
                "Implement approved plans by understanding and following existing code patterns, "
                "architectural decisions, and testing strategies. Reference and modify specific "
                "files as needed. Write clean, well-tested code that integrates seamlessly "
                "with the existing codebase. Include comprehensive tests and proper error handling."
            )
            
            additional_context = (
                f"Repository: {self.repository_root}\n"
                f"Trace ID: {trace_id}\n"
                "You have full access to the repository and can understand the complete "
                "codebase context for accurate implementation."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                system_prompt=system_prompt,
                additional_context=additional_context
            )
            
            # Parse and validate implementation response
            parsed_response = self._parse_implementation_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "implementation",
                "repository_context": response.repository_context,
                "command_used": response.command_used
            }
            
            logger.info(f"Completed repository-aware implementation generation for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeCLIError:
            raise
        except Exception as e:
            raise ClaudeCLIError(f"Implementation generation failed for trace_id {trace_id}: {str(e)}")
    
    def _parse_triage_response(self, content: str, trace_id: str) -> Dict[str, Any]:
        """Parse and validate triage response format."""
        required_sections = [
            "Problem Summary",
            "Suspected Cause", 
            "Clarifying Questions",
            "Recommendation"
        ]
        
        parsed = self._parse_structured_response(content, required_sections, "triage", trace_id)
        
        # Validate recommendation
        recommendation = parsed.get("recommendation", "").lower()
        if "proceed" not in recommendation and "block" not in recommendation:
            raise ClaudeResponseValidationError(
                f"Triage recommendation must contain 'proceed' or 'block' (trace_id: {trace_id})"
            )
        
        return parsed
    
    def _parse_planning_response(self, content: str, trace_id: str) -> Dict[str, Any]:
        """Parse and validate planning response format."""
        required_sections = [
            "Proposed Approach",
            "Affected Files",
            "Acceptance Criteria",
            "Unit Test Plan",
            "Risks and Considerations",
            "Effort Estimate"
        ]
        
        parsed = self._parse_structured_response(content, required_sections, "planning", trace_id)
        
        # Validate affected files section
        affected_files = parsed.get("affected_files", "")
        if not affected_files or len(affected_files.strip()) < 10:
            raise ClaudeResponseValidationError(
                f"Planning response must include specific affected files (trace_id: {trace_id})"
            )
        
        return parsed
    
    def _parse_prioritization_response(self, content: str, trace_id: str) -> Dict[str, Any]:
        """Parse and validate prioritization response format."""
        required_sections = [
            "Expected User Value",
            "Implementation Effort", 
            "Risk Assessment",
            "Priority Recommendation",
            "Justification"
        ]
        
        parsed = self._parse_structured_response(content, required_sections, "prioritization", trace_id)
        
        # Validate priority recommendation
        priority_rec = parsed.get("priority_recommendation", "").lower()
        valid_priorities = ["p0", "p1", "p2"]
        if not any(priority in priority_rec for priority in valid_priorities):
            raise ClaudeResponseValidationError(
                f"Priority recommendation must include p0, p1, or p2 (trace_id: {trace_id})"
            )
        
        return parsed
    
    def _parse_implementation_response(self, content: str, trace_id: str) -> Dict[str, Any]:
        """Parse and validate implementation response format."""
        # Implementation responses are more flexible but should contain code
        if len(content.strip()) < 100:
            raise ClaudeResponseValidationError(
                f"Implementation response too short (trace_id: {trace_id})"
            )
        
        # Look for code blocks or structured implementation
        if "```" not in content and "def " not in content and "class " not in content:
            raise ClaudeResponseValidationError(
                f"Implementation response must contain code (trace_id: {trace_id})"
            )
        
        return {
            "implementation_content": content,
            "has_code_blocks": "```" in content,
            "estimated_lines": len(content.split('\n')),
            "repository_aware": True
        }
    
    def _parse_structured_response(
        self, 
        content: str, 
        required_sections: List[str], 
        workflow_type: str, 
        trace_id: str
    ) -> Dict[str, Any]:
        """Parse structured response with required sections."""
        parsed = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a section header
            section_found = None
            for section in required_sections:
                if line.startswith(f"- {section}:") or line.startswith(f"{section}:"):
                    section_found = section
                    break
            
            if section_found:
                # Save previous section if exists
                if current_section:
                    section_key = current_section.lower().replace(" ", "_")
                    parsed[section_key] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_found
                current_content = []
                
                # Extract content after colon
                colon_index = line.find(':')
                if colon_index != -1 and colon_index < len(line) - 1:
                    remaining_content = line[colon_index + 1:].strip()
                    if remaining_content:
                        current_content.append(remaining_content)
            
            elif current_section and line:
                current_content.append(line)
        
        # Save final section
        if current_section:
            section_key = current_section.lower().replace(" ", "_")
            parsed[section_key] = '\n'.join(current_content).strip()
        
        # Validate all required sections are present
        missing_sections = []
        for section in required_sections:
            section_key = section.lower().replace(" ", "_")
            if section_key not in parsed or not parsed[section_key]:
                missing_sections.append(section)
        
        if missing_sections:
            raise ClaudeResponseValidationError(
                f"{workflow_type.title()} response missing required sections: {missing_sections} (trace_id: {trace_id})"
            )
        
        return parsed


def get_claude_cli_client(repository_root: Optional[str] = None) -> ClaudeCLIClient:
    """
    Factory function to create a configured Claude CLI client.
    
    Args:
        repository_root: Path to repository root (defaults to current directory)
    
    Returns:
        Configured ClaudeCLIClient instance
        
    Raises:
        ClaudeCLIError: If client creation fails
    """
    return ClaudeCLIClient(repository_root=repository_root)