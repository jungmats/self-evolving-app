# Prompt Templates

This directory contains the prompt templates used by the Policy & Gate Component to generate constrained prompts for Claude at each workflow stage.

## Directory Structure

```
templates/
├── prompts/
│   ├── triage.txt      # Triage stage prompt template
│   ├── plan.txt        # Planning stage prompt template
│   ├── prioritize.txt  # Prioritization stage prompt template
│   └── implement.txt   # Implementation stage prompt template
└── README.md           # This file
```

## Template Variables

All templates support the following variables that are automatically substituted:

### Common Variables
- `{request_type}` - Type of request (bug, feature, investigate)
- `{source}` - Source of request (user, monitor)
- `{issue_content}` - The full content of the GitHub Issue
- `{trace_id}` - Unique trace ID for audit trail
- `{constraints}` - Policy-generated constraints for the stage

### Stage-Specific Variables
- `{priority}` - Priority level (available in plan, prioritize, implement stages)
- `{severity}` - Severity level (available for bug requests in plan, prioritize, implement stages)

## Template Loading

The Policy & Gate Component uses a **fail-fast approach** for template loading:

1. **Required Templates** - All four stage templates must exist: `triage.txt`, `plan.txt`, `prioritize.txt`, `implement.txt`
2. **Template Validation** - Each template must contain required variables: `{request_type}`, `{source}`, `{issue_content}`, `{trace_id}`, `{constraints}`
3. **No Fallbacks** - If any template is missing or invalid, the system will raise a `TemplateLoadError` and refuse to start
4. **Explicit Errors** - Clear error messages indicate exactly which templates are missing or what variables are missing

This ensures that the system never operates with incomplete or invalid prompt templates, following the "Fail Fast, No Silent Fallbacks" principle.

## Customizing Templates

To customize a prompt template:

1. Edit the appropriate `.txt` file in `templates/prompts/`
2. Ensure all required variables are included (see above)
3. Test your changes by running the policy component
4. The changes take effect immediately (no restart required)

## Template Guidelines

When editing templates, follow these guidelines:

### Structure
- Start with a clear role definition for Claude
- Include all context sections (ISSUE CONTENT, TRACE_ID, CONSTRAINTS)
- End with specific output format requirements

### Variables
- Always include `{request_type}`, `{source}`, `{issue_content}`, `{trace_id}`, `{constraints}`
- Use conditional variables like `{priority}` and `{severity}` appropriately
- Variables are case-sensitive and must match exactly

### Constraints Section
The `{constraints}` variable is populated by the Policy & Gate Component with:
- Stage-specific scope limits
- Output format requirements
- Maximum response length
- Custom policy constraints (if extended)

### Output Format
Each template should specify a clear output format that:
- Is structured and consistent
- Matches the stage's purpose
- Can be parsed by downstream processes
- Includes all required information for the next stage

## Example Template Structure

```
You are [role description] for a {request_type} request from {source} source.

ISSUE CONTENT:
{issue_content}

TRACE_ID: {trace_id}
[Additional context variables as needed]

CONSTRAINTS:
{constraints}

[Specific instructions for this stage]

Provide your [output type] in the following format:
- [Required section 1]: [Description]
- [Required section 2]: [Description]
- [Additional sections as needed]
```

## Error Handling

### Template Loading Errors

The system will raise a `TemplateLoadError` in these cases:

- **Missing template directory**: `templates/prompts/` doesn't exist
- **Missing template files**: Any of the four required `.txt` files is missing
- **Empty template files**: Template files exist but are empty
- **Invalid templates**: Templates missing required variables
- **File read errors**: Permission issues or file corruption

### Required Variables

Every template MUST include these variables:
- `{request_type}` - Type of request (bug, feature, investigate)
- `{source}` - Source of request (user, monitor)  
- `{issue_content}` - The full GitHub Issue content
- `{trace_id}` - Unique trace ID for audit trail
- `{constraints}` - Policy-generated constraints

Missing any of these variables will cause a `TemplateLoadError` on startup.

### Troubleshooting

If you encounter template loading errors:

1. **Check file existence**: Ensure all four template files exist in `templates/prompts/`
2. **Verify file permissions**: Make sure files are readable
3. **Validate variables**: Check that all required variables are present in each template
4. **Check file encoding**: Templates should be UTF-8 encoded
5. **Review error message**: The error will specify exactly what's missing or invalid

## Testing Templates

To test template changes:

```python
from app.policy_gate import PolicyGateComponent, TemplateLoadError
from app.models import StageContext

try:
    # Create policy component (will fail fast if templates are invalid)
    policy = PolicyGateComponent(db_session=None)
    
    # Create test context
    context = StageContext(
        issue_id=123,
        current_stage="triage",  # Change to test different stages
        request_type="feature",
        source="user",
        trace_id="test-123",
        issue_content="Test issue content",
        workflow_artifacts=[]
    )
    
    # Generate prompt
    decision = policy.evaluate_stage_transition(context)
    if decision.decision == "allow":
        print(decision.constructed_prompt)
        
except TemplateLoadError as e:
    print(f"Template loading failed: {e}")
```

## Version Control

Template files are version controlled along with the code. When making changes:

1. Test thoroughly with various request types
2. Document significant changes in commit messages
3. Consider backward compatibility with existing workflows
4. Update this README if adding new variables or changing structure