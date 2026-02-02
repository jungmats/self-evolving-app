"""Claude API client for the Self-Evolving Web Application.

This module provides a client for interacting with Claude API with constrained prompt handling,
workflow-specific prompt templates, and response parsing and validation.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ClaudeClientError(Exception):
    """Custom exception for Claude client errors."""
    pass


class ClaudeResponseValidationError(ClaudeClientError):
    """Raised when Claude response doesn't meet validation requirements."""
    pass


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    content: str
    usage: Dict[str, int]
    model: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "usage": self.usage,
            "model": self.model,
            "timestamp": self.timestamp.isoformat()
        }


class ClaudeClient:
    """
    Claude API client with constrained prompt handling and response validation.
    
    Provides methods for workflow-specific Claude interactions with proper error handling,
    response parsing, and validation against expected output formats.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229", timeout: int = 60):
        """
        Initialize Claude client.
        
        Args:
            api_key: Claude API key (defaults to CLAUDE_API_KEY env var)
            model: Claude model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1"
        
        if not self.api_key:
            raise ClaudeClientError("Claude API key is required. Set CLAUDE_API_KEY environment variable.")
        
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None
    ) -> ClaudeResponse:
        """
        Generate response from Claude API.
        
        Args:
            prompt: User prompt to send to Claude
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 = deterministic, 1.0 = creative)
            system_prompt: Optional system prompt for context
            
        Returns:
            ClaudeResponse with content and metadata
            
        Raises:
            ClaudeClientError: If API request fails
        """
        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Handle API errors
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                raise ClaudeClientError(f"Claude API error: {error_msg}")
            
            # Parse response
            response_data = response.json()
            
            # Extract content from response
            content = ""
            if "content" in response_data and response_data["content"]:
                # Handle both single content and array of content blocks
                if isinstance(response_data["content"], list):
                    content = "".join(block.get("text", "") for block in response_data["content"] if block.get("type") == "text")
                else:
                    content = response_data["content"]
            
            # Extract usage information
            usage = response_data.get("usage", {})
            
            return ClaudeResponse(
                content=content.strip(),
                usage=usage,
                model=response_data.get("model", self.model),
                timestamp=datetime.utcnow()
            )
            
        except requests.exceptions.Timeout:
            raise ClaudeClientError(f"❌ Claude API request timed out after {self.timeout} seconds. Check network connectivity.")
        except requests.exceptions.RequestException as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                raise ClaudeClientError("❌ Claude API authentication failed. Check your CLAUDE_API_KEY.")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                raise ClaudeClientError("❌ Claude API rate limit exceeded. Please try again later.")
            else:
                raise ClaudeClientError(f"❌ Claude API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise ClaudeClientError(f"❌ Failed to parse Claude API response: {str(e)}")
        except Exception as e:
            raise ClaudeClientError(f"❌ Unexpected error calling Claude API: {str(e)}")
    
    def triage_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform triage analysis using Claude.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed triage analysis with structured fields
            
        Raises:
            ClaudeClientError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting triage analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a technical triage analyst. Analyze the provided issue and respond "
                "in the exact format requested. Be concise but thorough. Focus only on "
                "understanding the problem, not on implementation."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                max_tokens=2000,
                temperature=0.1,
                system_prompt=system_prompt
            )
            
            # Parse and validate triage response
            parsed_response = self._parse_triage_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "usage": response.usage,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "triage"
            }
            
            logger.info(f"Completed triage analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeClientError:
            raise
        except Exception as e:
            raise ClaudeClientError(f"Triage analysis failed for trace_id {trace_id}: {str(e)}")
    
    def planning_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform planning analysis using Claude.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed planning analysis with structured fields
            
        Raises:
            ClaudeClientError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting planning analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a technical architect. Create detailed implementation plans "
                "without writing actual code. Focus on approach, design, and testing strategy. "
                "Respond in the exact format requested."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                max_tokens=3000,
                temperature=0.1,
                system_prompt=system_prompt
            )
            
            # Parse and validate planning response
            parsed_response = self._parse_planning_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "usage": response.usage,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "planning"
            }
            
            logger.info(f"Completed planning analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeClientError:
            raise
        except Exception as e:
            raise ClaudeClientError(f"Planning analysis failed for trace_id {trace_id}: {str(e)}")
    
    def prioritization_analysis(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Perform prioritization analysis using Claude.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed prioritization analysis with structured fields
            
        Raises:
            ClaudeClientError: If analysis fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting prioritization analysis for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a product manager assessing priorities. Evaluate user value, "
                "effort, and risk to recommend priority levels. Do not make implementation "
                "decisions. Respond in the exact format requested."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                max_tokens=1500,
                temperature=0.1,
                system_prompt=system_prompt
            )
            
            # Parse and validate prioritization response
            parsed_response = self._parse_prioritization_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "usage": response.usage,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "prioritization"
            }
            
            logger.info(f"Completed prioritization analysis for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeClientError:
            raise
        except Exception as e:
            raise ClaudeClientError(f"Prioritization analysis failed for trace_id {trace_id}: {str(e)}")
    
    def implementation_generation(self, constrained_prompt: str, trace_id: str) -> Dict[str, Any]:
        """
        Generate implementation using Claude.
        
        Args:
            constrained_prompt: Policy-constrained prompt from PolicyGateComponent
            trace_id: Trace ID for logging and correlation
            
        Returns:
            Parsed implementation with code and tests
            
        Raises:
            ClaudeClientError: If generation fails
            ClaudeResponseValidationError: If response format is invalid
        """
        try:
            logger.info(f"Starting implementation generation for trace_id: {trace_id}")
            
            system_prompt = (
                "You are a senior software engineer implementing approved plans. "
                "Write clean, well-tested code following existing patterns. "
                "Include comprehensive tests and proper error handling."
            )
            
            response = self.generate_response(
                prompt=constrained_prompt,
                max_tokens=10000,
                temperature=0.1,
                system_prompt=system_prompt
            )
            
            # Parse and validate implementation response
            parsed_response = self._parse_implementation_response(response.content, trace_id)
            
            # Add metadata
            parsed_response["_metadata"] = {
                "trace_id": trace_id,
                "model": response.model,
                "usage": response.usage,
                "timestamp": response.timestamp.isoformat(),
                "workflow_stage": "implementation"
            }
            
            logger.info(f"Completed implementation generation for trace_id: {trace_id}")
            return parsed_response
            
        except ClaudeResponseValidationError:
            raise
        except ClaudeClientError:
            raise
        except Exception as e:
            raise ClaudeClientError(f"Implementation generation failed for trace_id {trace_id}: {str(e)}")
    
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
            "estimated_lines": len(content.split('\n'))
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


def get_claude_client() -> ClaudeClient:
    """
    Factory function to create a configured Claude client.
    
    Returns:
        Configured ClaudeClient instance
        
    Raises:
        ClaudeClientError: If client creation fails
    """
    return ClaudeClient()