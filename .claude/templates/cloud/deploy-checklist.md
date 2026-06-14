---
model: claude-sonnet-4-0
complexity: intermediate
priority: critical
tags: [deploy, ci, cloud, infra]
depends_on: []
chains_to: []
skip_if: [no_ci]
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Deployment Checklist and Configuration

Generate deployment configuration and checklist for: $ARGUMENTS

Create comprehensive deployment artifacts:

1. **Pre-Deployment Checklist**:
   - [ ] All tests passing
   - [ ] Security scan completed
   - [ ] Performance benchmarks met
   - [ ] Documentation updated
   - [ ] Database migrations tested
   - [ ] Rollback plan documented
   - [ ] Monitoring alerts configured
   - [ ] Load testing completed

2. **Infrastructure Configuration**:
   - {{CLOUD_CONTAINER_TOOL}}/containerization setup
   - {{CLOUD_ORCHESTRATOR}} manifests
   - {{CLOUD_IAC_TOOL}}/IaC scripts
   - Environment variables
   - Secrets management
   - Network policies
   - Auto-scaling rules

3. **CI/CD Pipeline**:
   - {{CLOUD_CI_TOOL}}/{{CLOUD_CI_TOOL}}
   - Build optimization
   - Test parallelization
   - Security scanning
   - Image building
   - Deployment stages
   - Rollback automation

4. **Database Deployment**:
   - Migration scripts
   - Backup procedures
   - Connection pooling
   - Read replica setup
   - Failover configuration
   - Data seeding
   - Version compatibility

5. **Monitoring Setup**:
   - Application metrics
   - Infrastructure metrics
   - Log aggregation
   - Error tracking
   - Uptime monitoring
   - Custom dashboards
   - Alert channels

6. **Security Configuration**:
   - SSL/TLS setup
   - API key rotation
   - CORS policies
   - Rate limiting
   - WAF rules
   - Security headers
   - Vulnerability scanning

7. **Post-Deployment**:
   - [ ] Smoke tests
   - [ ] Performance validation
   - [ ] Monitoring verification
   - [ ] Documentation published
   - [ ] Team notification
   - [ ] Customer communication
   - [ ] Metrics baseline

Include environment-specific configurations (dev, staging, prod) and disaster recovery procedures.
