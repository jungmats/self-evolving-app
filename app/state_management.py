"""Issue state management for the Self-Evolving Web Application."""

from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from app.github_client import GitHubClient, GitHubClientError
import logging

logger = logging.getLogger(__name__)


class Stage(Enum):
    """Valid workflow stages."""
    TRIAGE = "stage:triage"
    PLAN = "stage:plan"
    PRIORITIZE = "stage:prioritize"
    AWAITING_IMPLEMENTATION_APPROVAL = "stage:awaiting-implementation-approval"
    IMPLEMENT = "stage:implement"
    PR_OPENED = "stage:pr-opened"
    AWAITING_DEPLOY_APPROVAL = "stage:awaiting-deploy-approval"
    BLOCKED = "stage:blocked"
    DONE = "stage:done"


class RequestType(Enum):
    """Valid request types."""
    BUG = "request:bug"
    FEATURE = "request:feature"
    INVESTIGATE = "request:investigate"


class Source(Enum):
    """Valid request sources."""
    USER = "source:user"
    MONITOR = "source:monitor"


class Priority(Enum):
    """Valid priority levels."""
    P0 = "priority:p0"
    P1 = "priority:p1"
    P2 = "priority:p2"


class StateTransitionError(Exception):
    """Exception raised for invalid state transitions."""
    pass


class IssueStateManager:
    """
    Manages GitHub Issue state transitions and label management.
    
    Ensures state machine integrity and provides audit trail through comments.
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        Stage.TRIAGE: [Stage.PLAN, Stage.BLOCKED],
        Stage.PLAN: [Stage.PRIORITIZE, Stage.BLOCKED],
        Stage.PRIORITIZE: [Stage.AWAITING_IMPLEMENTATION_APPROVAL],
        Stage.AWAITING_IMPLEMENTATION_APPROVAL: [Stage.IMPLEMENT, Stage.BLOCKED],
        Stage.IMPLEMENT: [Stage.PR_OPENED, Stage.BLOCKED],
        Stage.PR_OPENED: [Stage.AWAITING_DEPLOY_APPROVAL],
        Stage.AWAITING_DEPLOY_APPROVAL: [Stage.DONE, Stage.BLOCKED],
        Stage.BLOCKED: [Stage.TRIAGE],  # Manual intervention can restart from triage
    }
    
    # Required labels for repository setup
    REQUIRED_LABELS = [
        # Stage labels
        {"name": "stage:triage", "color": "0052cc", "description": "Issue is being triaged"},
        {"name": "stage:plan", "color": "1d76db", "description": "Issue is being planned"},
        {"name": "stage:prioritize", "color": "5319e7", "description": "Issue is being prioritized"},
        {"name": "stage:awaiting-implementation-approval", "color": "fbca04", "description": "Awaiting human approval for implementation"},
        {"name": "stage:implement", "color": "0e8a16", "description": "Issue is being implemented"},
        {"name": "stage:pr-opened", "color": "006b75", "description": "Pull request has been opened"},
        {"name": "stage:awaiting-deploy-approval", "color": "f9d0c4", "description": "Awaiting human approval for deployment"},
        {"name": "stage:blocked", "color": "d93f0b", "description": "Issue is blocked"},
        {"name": "stage:done", "color": "0e8a16", "description": "Issue is complete"},
        
        # Request type labels
        {"name": "request:bug", "color": "d73a4a", "description": "Bug report"},
        {"name": "request:feature", "color": "a2eeef", "description": "Feature request"},
        {"name": "request:investigate", "color": "7057ff", "description": "Investigation request from monitoring"},
        
        # Source labels
        {"name": "source:user", "color": "c2e0c6", "description": "Request from user"},
        {"name": "source:monitor", "color": "fef2c0", "description": "Request from monitoring system"},
        
        # Priority labels
        {"name": "priority:p0", "color": "b60205", "description": "Critical priority"},
        {"name": "priority:p1", "color": "d93f0b", "description": "High priority"},
        {"name": "priority:p2", "color": "fbca04", "description": "Medium priority"},
        
        # Agent labels
        {"name": "agent:claude", "color": "e99695", "description": "Created or modified by Claude"},
    ]
    
    def __init__(self, github_client: GitHubClient):
        """
        Initialize state manager with GitHub client.
        
        Args:
            github_client: Configured GitHubClient instance
        """
        self.github_client = github_client
    
    def ensure_repository_labels(self) -> None:
        """
        Ensure all required labels exist in the repository.
        
        Raises:
            GitHubClientError: If label creation fails
        """
        self.github_client.ensure_labels_exist(self.REQUIRED_LABELS)
        logger.info("Ensured all required labels exist in repository")
    
    def create_issue_with_initial_state(
        self,
        title: str,
        description: str,
        request_type: RequestType,
        source: Source,
        trace_id: str,
        severity: Optional[str] = None,
        priority: Optional[str] = None
    ) -> int:
        """
        Create a GitHub Issue with initial state and proper labeling.
        
        Args:
            title: Issue title
            description: Issue description
            request_type: Type of request (bug, feature, investigate)
            source: Source of request (user, monitor)
            trace_id: Unique Trace_ID for linking
            severity: Bug severity (for bug reports)
            priority: Feature priority (for feature requests)
            
        Returns:
            GitHub Issue number
            
        Raises:
            GitHubClientError: If issue creation fails
        """
        # Build enhanced description with metadata
        enhanced_description = description
        if severity and request_type == RequestType.BUG:
            enhanced_description = f"**Severity**: {severity}\n\n{description}"
        elif priority and request_type == RequestType.FEATURE:
            enhanced_description = f"**Priority**: {priority}\n\n{description}"
        
        # Initial labels: request type, source, and initial stage
        initial_labels = [
            request_type.value,
            source.value,
            Stage.TRIAGE.value
        ]
        
        # Create the issue
        issue = self.github_client.create_issue(
            title=title,
            body=enhanced_description,
            labels=initial_labels,
            trace_id=trace_id
        )
        
        # Add initial state transition comment
        self._add_state_transition_comment(
            issue.number,
            None,
            Stage.TRIAGE,
            f"Issue created with Trace_ID: {trace_id}",
            trace_id
        )
        
        logger.info(f"Created Issue #{issue.number} in {Stage.TRIAGE.value} state with Trace_ID: {trace_id}")
        return issue.number
    
    def transition_issue_state(
        self,
        issue_number: int,
        new_stage: Stage,
        reason: str,
        trace_id: str
    ) -> None:
        """
        Transition an Issue to a new stage with validation.
        
        Args:
            issue_number: GitHub Issue number
            new_stage: Target stage
            reason: Reason for transition
            trace_id: Trace_ID for audit trail
            
        Raises:
            StateTransitionError: If transition is invalid
            GitHubClientError: If GitHub operations fail
        """
        # Get current issue state
        issue = self.github_client.get_issue(issue_number)
        current_stage = self._get_current_stage(issue)
        
        # Validate transition
        if current_stage and new_stage not in self.VALID_TRANSITIONS.get(current_stage, []):
            raise StateTransitionError(
                f"Invalid transition from {current_stage.value} to {new_stage.value}"
            )
        
        # Get current labels and update stage label
        current_labels = [label.name for label in issue.labels]
        new_labels = [label for label in current_labels if not label.startswith("stage:")]
        new_labels.append(new_stage.value)
        
        # Update labels
        self.github_client.set_issue_labels(issue_number, new_labels)
        
        # Add transition comment
        self._add_state_transition_comment(
            issue_number,
            current_stage,
            new_stage,
            reason,
            trace_id
        )
        
        logger.info(f"Transitioned Issue #{issue_number} from {current_stage.value if current_stage else 'None'} to {new_stage.value}")
    
    def add_priority_label(self, issue_number: int, priority: Priority, trace_id: str) -> None:
        """
        Add priority label to an Issue.
        
        Args:
            issue_number: GitHub Issue number
            priority: Priority level
            trace_id: Trace_ID for audit trail
        """
        # Remove existing priority labels first
        issue = self.github_client.get_issue(issue_number)
        current_labels = [label.name for label in issue.labels]
        new_labels = [label for label in current_labels if not label.startswith("priority:")]
        new_labels.append(priority.value)
        
        self.github_client.set_issue_labels(issue_number, new_labels)
        
        # Add comment for audit trail
        comment = f"Priority set to {priority.value}\n\n**Trace_ID**: `{trace_id}`\n**Timestamp**: {datetime.utcnow().isoformat()}Z"
        self.github_client.add_issue_comment(issue_number, comment)
        
        logger.info(f"Added priority {priority.value} to Issue #{issue_number}")
    
    def get_issue_stage(self, issue_number: int) -> Optional[Stage]:
        """
        Get the current stage of an Issue.
        
        Args:
            issue_number: GitHub Issue number
            
        Returns:
            Current stage or None if no stage label found
        """
        issue = self.github_client.get_issue(issue_number)
        return self._get_current_stage(issue)
    
    def _get_current_stage(self, issue) -> Optional[Stage]:
        """
        Extract current stage from Issue labels.
        
        Args:
            issue: GitHub Issue object
            
        Returns:
            Current Stage or None if no stage label found
        """
        for label in issue.labels:
            for stage in Stage:
                if label.name == stage.value:
                    return stage
        return None
    
    def _add_state_transition_comment(
        self,
        issue_number: int,
        from_stage: Optional[Stage],
        to_stage: Stage,
        reason: str,
        trace_id: str
    ) -> None:
        """
        Add a state transition comment for audit trail.
        
        Args:
            issue_number: GitHub Issue number
            from_stage: Previous stage (None for initial state)
            to_stage: New stage
            reason: Reason for transition
            trace_id: Trace_ID for linking
        """
        from_text = from_stage.value if from_stage else "None"
        comment = f"""**State Transition**: {from_text} → {to_stage.value}

**Reason**: {reason}

**Trace_ID**: `{trace_id}`
**Timestamp**: {datetime.utcnow().isoformat()}Z"""
        
        self.github_client.add_issue_comment(issue_number, comment)


def get_state_manager(github_client: GitHubClient) -> IssueStateManager:
    """
    Factory function to create a configured IssueStateManager.
    
    Args:
        github_client: Configured GitHubClient instance
        
    Returns:
        Configured IssueStateManager instance
    """
    return IssueStateManager(github_client)