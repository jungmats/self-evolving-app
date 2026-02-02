# Policy & Gate Component Extension Guide

This guide explains how to extend the Policy & Gate Component with custom rules and organization-specific policies.

## Overview

The Policy & Gate Component provides a base layer of safety and validation checks, but you can extend it with custom rules that align with your organization's mission, business requirements, and compliance needs.

## Architecture

The policy system uses a layered approach:

1. **Base Policy Layer** - Core safety, validation, and stage constraints
2. **Custom Policy Layer** - Organization-specific rules and checks
3. **Prompt Enhancement** - Custom constraints added to Claude prompts

## Extension Methods

### Method 1: Subclassing PolicyGateComponent

Create a custom policy class that extends the base component:

```python
from app.policy_gate import PolicyGateComponent
from app.models import StageContext, PolicyDecisionModel
from typing import Dict, Any

class CustomPolicyGateComponent(PolicyGateComponent):
    """Extended policy component with custom rules."""
    
    def __init__(self, db_session=None):
        super().__init__(db_session)
        self._custom_config = self._load_custom_config()
    
    def evaluate_stage_transition(self, context: StageContext) -> PolicyDecisionModel:
        """Override to add custom policy checks."""
        # Run base policy checks first
        base_decision = super().evaluate_stage_transition(context)
        
        # If base policy blocks/requires review, return that
        if base_decision.decision != "allow":
            return base_decision
        
        # Run custom policy checks
        custom_check = self._evaluate_custom_policies(context)
        if custom_check["decision"] != "allow":
            return PolicyDecisionModel(
                decision=custom_check["decision"],
                reason=custom_check["reason"],
                constraints=custom_check["constraints"]
            )
        
        # Enhance prompt with custom constraints
        if base_decision.constructed_prompt:
            base_decision.constructed_prompt = self._enhance_prompt(
                base_decision.constructed_prompt, context
            )
        
        return base_decision
```

### Method 2: Configuration-Based Extension

Modify the base component's configuration methods:

```python
def _load_stage_constraints(self) -> Dict[str, Any]:
    """Override to add custom stage constraints."""
    base_constraints = super()._load_stage_constraints()
    
    # Add custom constraints
    base_constraints["triage"]["custom_checks"] = ["mission_alignment"]
    base_constraints["plan"]["custom_checks"] = ["business_value", "security_review"]
    
    return base_constraints
```

## Common Extension Patterns

### 1. Mission Alignment Checks

Ensure requests align with organizational mission:

```python
def _check_mission_alignment(self, content: str) -> Dict[str, Any]:
    """Check if request aligns with mission statement."""
    mission_keywords = {
        "positive": ["automation", "security", "reliability", "transparency"],
        "negative": ["bypass approval", "skip review", "disable security"]
    }
    
    # Check for anti-mission patterns
    violations = [kw for kw in mission_keywords["negative"] if kw in content.lower()]
    if violations:
        return {
            "decision": "block",
            "reason": f"Conflicts with mission: {', '.join(violations)}",
            "constraints": {"mission_violations": violations}
        }
    
    # Check for positive alignment
    alignments = [kw for kw in mission_keywords["positive"] if kw in content.lower()]
    if len(alignments) == 0:
        return {
            "decision": "review_required",
            "reason": "Unclear mission alignment, requires review",
            "constraints": {"mission_alignment": "unclear"}
        }
    
    return {"decision": "allow", "reason": "Mission aligned", "constraints": {}}
```

### 2. Business Value Validation

Require feature requests to articulate business value:

```python
def _check_business_value(self, content: str, request_type: str) -> Dict[str, Any]:
    """Validate business value articulation for features."""
    if request_type != "feature":
        return {"decision": "allow", "reason": "N/A for non-features", "constraints": {}}
    
    value_indicators = ["user", "benefit", "improve", "reduce", "save", "efficiency"]
    found_indicators = [word for word in value_indicators if word in content.lower()]
    
    if len(found_indicators) < 2:
        return {
            "decision": "review_required",
            "reason": "Feature lacks clear business value",
            "constraints": {
                "business_value": "unclear",
                "suggestion": "Describe user benefit and business impact"
            }
        }
    
    return {"decision": "allow", "reason": "Business value clear", "constraints": {}}
```

### 3. Security Pattern Enforcement

Block security anti-patterns and enforce security considerations:

```python
def _check_security_patterns(self, content: str) -> Dict[str, Any]:
    """Check for security patterns and anti-patterns."""
    anti_patterns = [
        "disable ssl", "skip validation", "hardcode password", 
        "trust user input", "bypass security"
    ]
    
    violations = [pattern for pattern in anti_patterns if pattern in content.lower()]
    if violations:
        return {
            "decision": "block",
            "reason": f"Security anti-patterns: {', '.join(violations)}",
            "constraints": {"security_violations": violations}
        }
    
    # For security-related requests, ensure proper consideration
    if any(word in content.lower() for word in ["security", "auth", "login", "password"]):
        security_keywords = ["authentication", "authorization", "encryption", "validation"]
        found_keywords = [kw for kw in security_keywords if kw in content.lower()]
        
        if len(found_keywords) < 1:
            return {
                "decision": "review_required",
                "reason": "Security request needs security considerations",
                "constraints": {"security_review": "required"}
            }
    
    return {"decision": "allow", "reason": "Security patterns OK", "constraints": {}}
```

### 4. Compliance and Regulatory Checks

Add compliance-specific validation:

```python
def _check_compliance_requirements(self, content: str, context: StageContext) -> Dict[str, Any]:
    """Check compliance and regulatory requirements."""
    
    # Check for data privacy implications
    privacy_keywords = ["personal data", "user data", "pii", "gdpr", "privacy"]
    if any(keyword in content.lower() for keyword in privacy_keywords):
        return {
            "decision": "review_required",
            "reason": "Data privacy implications require compliance review",
            "constraints": {
                "compliance_review": "privacy",
                "required_approvals": ["data_protection_officer", "legal"]
            }
        }
    
    # Check for financial/payment implications
    financial_keywords = ["payment", "billing", "financial", "money", "transaction"]
    if any(keyword in content.lower() for keyword in financial_keywords):
        return {
            "decision": "review_required",
            "reason": "Financial implications require compliance review",
            "constraints": {
                "compliance_review": "financial",
                "required_approvals": ["finance", "security"]
            }
        }
    
    return {"decision": "allow", "reason": "No compliance issues", "constraints": {}}
```

## Prompt Enhancement

Enhance Claude prompts with custom constraints:

```python
def _enhance_prompt_with_custom_constraints(self, base_prompt: str, context: StageContext) -> str:
    """Add custom constraints to Claude prompts."""
    custom_constraints = []
    
    # Add mission alignment constraint
    custom_constraints.append(
        "MISSION ALIGNMENT: Ensure all analysis aligns with our mission of "
        "controlled automation with human oversight, security, and transparency."
    )
    
    # Add business value constraint for features
    if context.request_type == "feature":
        custom_constraints.append(
            "BUSINESS VALUE: Clearly articulate user benefits, business impact, "
            "and ROI considerations in your analysis."
        )
    
    # Add security constraint if relevant
    security_keywords = ["security", "auth", "login", "password", "token"]
    if any(keyword in context.issue_content.lower() for keyword in security_keywords):
        custom_constraints.append(
            "SECURITY FOCUS: Pay special attention to security implications, "
            "authentication, authorization, and data protection requirements."
        )
    
    if custom_constraints:
        return base_prompt + "\n\nCUSTOM CONSTRAINTS:\n" + "\n".join(custom_constraints)
    
    return base_prompt
```

## Integration with Workflow System

### Update Policy Gate Evaluation Script

Modify `.github/scripts/policy_gate_evaluation.py` to use your custom policy:

```python
# Replace the standard policy component
from your_custom_module import CustomPolicyGateComponent

class PolicyGateEvaluator:
    def __init__(self, github_token=None, repository=None):
        # ... existing code ...
        
        # Use custom policy component instead of base
        self.policy_component = CustomPolicyGateComponent(self.db_session)
```

### Update Configuration Files

Create configuration files for your custom rules:

```json
// config/custom_policy_rules.json
{
  "mission_statement": "Build controlled automation with human oversight...",
  "mission_keywords": {
    "positive": ["automation", "security", "reliability", "transparency"],
    "negative": ["bypass approval", "skip review", "disable security"]
  },
  "business_value_requirements": {
    "enabled": true,
    "required_elements": ["user_benefit", "business_impact", "roi_consideration"]
  },
  "security_patterns": {
    "anti_patterns": ["disable ssl", "skip validation", "hardcode password"],
    "required_keywords": ["authentication", "authorization", "encryption"]
  },
  "compliance_triggers": {
    "privacy": ["personal data", "pii", "gdpr"],
    "financial": ["payment", "billing", "transaction"]
  }
}
```

## Testing Custom Policies

Create tests for your custom policy extensions:

```python
def test_custom_policy_mission_alignment():
    """Test mission alignment checks."""
    policy = CustomPolicyGateComponent(db_session=None)
    
    # Test mission-aligned request
    context = StageContext(
        issue_id=123,
        current_stage="triage",
        request_type="feature",
        source="user",
        trace_id="test-123",
        issue_content="Add automated security monitoring to improve system reliability",
        workflow_artifacts=[]
    )
    
    decision = policy.evaluate_stage_transition(context)
    assert decision.decision == "allow"
    
    # Test anti-mission request
    context.issue_content = "Add feature to bypass approval gates"
    decision = policy.evaluate_stage_transition(context)
    assert decision.decision == "block"
```

## Best Practices

### 1. Layered Approach
- Keep base safety checks intact
- Add custom rules as additional layers
- Maintain clear separation of concerns

### 2. Configuration-Driven
- Use configuration files for rules and keywords
- Make policies easily adjustable without code changes
- Version control your policy configurations

### 3. Comprehensive Testing
- Test all custom policy paths
- Include positive and negative test cases
- Test prompt enhancement functionality

### 4. Audit Trail
- Log all custom policy decisions
- Include reasoning and constraints
- Maintain traceability for compliance

### 5. Performance Considerations
- Keep custom checks efficient
- Cache configuration data
- Avoid complex regex or heavy processing

### 6. Documentation
- Document all custom rules and their rationale
- Provide examples of what passes/fails
- Keep policy documentation up to date

## Example: Complete Custom Policy Implementation

Here's a complete example that combines multiple extension patterns:

```python
from app.policy_gate import PolicyGateComponent
from app.models import StageContext, PolicyDecisionModel
import json
from typing import Dict, Any

class OrganizationPolicyGateComponent(PolicyGateComponent):
    """Organization-specific policy component with custom rules."""
    
    def __init__(self, db_session=None, config_path="config/policy_rules.json"):
        super().__init__(db_session)
        self._custom_config = self._load_custom_config(config_path)
    
    def _load_custom_config(self, config_path: str) -> Dict[str, Any]:
        """Load custom policy configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found."""
        return {
            "mission_alignment": {"enabled": True},
            "business_value": {"enabled": True},
            "security_patterns": {"enabled": True},
            "compliance_checks": {"enabled": True}
        }
    
    def evaluate_stage_transition(self, context: StageContext) -> PolicyDecisionModel:
        """Extended evaluation with all custom checks."""
        # Run base policy first
        base_decision = super().evaluate_stage_transition(context)
        
        if base_decision.decision != "allow":
            return base_decision
        
        # Run all custom checks
        for check_name, check_config in self._custom_config.items():
            if not check_config.get("enabled", False):
                continue
                
            check_method = getattr(self, f"_check_{check_name}", None)
            if check_method:
                result = check_method(context)
                if result["decision"] != "allow":
                    return PolicyDecisionModel(
                        decision=result["decision"],
                        reason=result["reason"],
                        constraints=result["constraints"]
                    )
        
        # Enhance prompt with all applicable constraints
        if base_decision.constructed_prompt:
            base_decision.constructed_prompt = self._enhance_prompt_with_all_constraints(
                base_decision.constructed_prompt, context
            )
        
        return base_decision
    
    # Implement individual check methods...
    def _check_mission_alignment(self, context: StageContext) -> Dict[str, Any]:
        # Implementation here...
        pass
    
    def _check_business_value(self, context: StageContext) -> Dict[str, Any]:
        # Implementation here...
        pass
    
    def _check_security_patterns(self, context: StageContext) -> Dict[str, Any]:
        # Implementation here...
        pass
    
    def _check_compliance_checks(self, context: StageContext) -> Dict[str, Any]:
        # Implementation here...
        pass
```

This approach provides a flexible, maintainable way to extend the Policy & Gate Component with organization-specific rules while preserving the base safety and validation functionality.