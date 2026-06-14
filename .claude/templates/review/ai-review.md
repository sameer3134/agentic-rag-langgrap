---
model: claude-sonnet-4-0
complexity: intermediate
priority: high
tags: ["review", "ai", "backend"]
depends_on: []
chains_to: []
skip_if: []
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# AI/ML Code Review

Perform a specialized AI/ML code review for: $ARGUMENTS

Conduct comprehensive review focusing on:

1. **Model Code Quality**:
   - Reproducibility checks
   - Random seed management
   - Data leakage detection
   - Train/test split validation
   - Feature engineering clarity

2. **AI Best Practices**:
   - Prompt injection prevention
   - Token limit handling
   - Cost optimization
   - Fallback strategies
   - Timeout management

3. **Data Handling**:
   - Privacy compliance (PII handling)
   - Data versioning
   - Preprocessing consistency
   - Batch processing efficiency
   - Memory optimization

4. **Model Management**:
   - Version control for models
   - A/B testing setup
   - Rollback capabilities
   - Performance benchmarks
   - Drift detection

5. **LLM-Specific Checks**:
   - Context window management
   - Prompt template security
   - Response validation
   - Streaming implementation
   - Rate limit handling

6. **Vector Database Review**:
   - Embedding consistency
   - Index optimization
   - Query performance
   - Metadata management
   - Backup strategies

7. **Production Readiness**:
   - GPU/CPU optimization
   - Batching strategies
   - Caching implementation
   - Monitoring hooks
   - Error recovery

8. **Testing Coverage**:
   - Unit tests for preprocessing
   - Integration tests for pipelines
   - Model performance tests
   - Edge case handling
   - Mocked LLM responses

Provide specific recommendations with severity levels (Critical/High/Medium/Low). Include code examples for improvements and links to relevant best practices.
