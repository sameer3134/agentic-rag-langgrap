---
model: claude-sonnet-4-0
description: Security Scan Report & Orchestration
complexity: advanced
priority: critical
tags: ["security", "review", "orchestration"]
depends_on: []
chains_to: ["backend/security-scan", "frontend/security-scan", "cloud/security-scan"]
skip_if: []
version: 1.0.0

---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Security Scan Report & Orchestration

This is the orchestration and reporting template for security scanning. It coordinates domain-specific scans and generates comprehensive security reports with actionable insights.

For domain-specific scanning, use the appropriate template:
- **Backend** (SAST, API security, secret detection, dependency scanning): `backend/security-scan.md`
- **Frontend** (XSS, CSRF, clickjacking, security headers, CSP): `frontend/security-scan.md`
- **Cloud** (IaC scanning, container security, CI/CD pipelines, infrastructure hardening): `cloud/security-scan.md`

## Requirements
$ARGUMENTS

## Instructions

### 1. Security Report Generation

Generate comprehensive security reports with actionable insights:

**Advanced Reporting System**
```python
import json
import jinja2
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SecurityMetrics:
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    tools_used: List[str]
    scan_duration: float
    coverage_percentage: float
    false_positive_rate: float

class SecurityReportGenerator:
    def __init__(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.DictLoader({
                'executive_summary': self.EXECUTIVE_TEMPLATE,
                'detailed_report': self.DETAILED_TEMPLATE,
                'dashboard': self.DASHBOARD_TEMPLATE
            })
        )
    
    EXECUTIVE_TEMPLATE = """
# Executive Security Assessment Report

**Assessment Date**: {{ timestamp }}
**Overall Risk Level**: {{ risk_level }}
**Confidence Score**: {{ confidence_score }}%

## Summary
- **Total Vulnerabilities**: {{ metrics.total_vulnerabilities }}
- **Critical**: {{ metrics.critical_count }} ({{ critical_percentage }}%)
- **High**: {{ metrics.high_count }} ({{ high_percentage }}%)
- **Medium**: {{ metrics.medium_count }} ({{ medium_percentage }}%)
- **Low**: {{ metrics.low_count }} ({{ low_percentage }}%)

## Risk Assessment
| Risk Category | Current Level | Target Level | Priority |
|---------------|---------------|--------------|----------|
{% for risk in risk_categories %}
| {{ risk.category }} | {{ risk.current }} | {{ risk.target }} | {{ risk.priority }} |
{% endfor %}

## Immediate Actions Required
{% for action in immediate_actions %}
{{ loop.index }}. **{{ action.title }}** ({{ action.effort }})
   - Impact: {{ action.impact }}
   - Timeline: {{ action.timeline }}
   - Owner: {{ action.owner }}
{% endfor %}

## Compliance Status
{% for framework in compliance_frameworks %}
- **{{ framework.name }}**: {{ framework.status }} ({{ framework.score }}/100)
{% endfor %}

## Investment Required
- **Immediate (0-30 days)**: {{ costs.immediate }}
- **Short-term (1-6 months)**: {{ costs.short_term }}
- **Long-term (6+ months)**: {{ costs.long_term }}
"""
    
    DETAILED_TEMPLATE = """
# Detailed Security Findings Report

## Vulnerability Details
{% for vuln in vulnerabilities %}
### {{ loop.index }}. {{ vuln.title }}

**Severity**: {{ vuln.severity }} | **Confidence**: {{ vuln.confidence }} | **Tool**: {{ vuln.tool }}

**Location**: `{{ vuln.file_path }}:{{ vuln.line_number }}`

**Description**: {{ vuln.description }}

**Impact**: {{ vuln.impact }}

**Remediation**:
```{{ vuln.language }}
{{ vuln.remediation_code }}
```

**References**:
{% for ref in vuln.references %}
- [{{ ref.title }}]({{ ref.url }})
{% endfor %}

---
{% endfor %}

## Tool Effectiveness Analysis
{% for tool in tool_analysis %}
### {{ tool.name }}
- **Vulnerabilities Found**: {{ tool.found_count }}
- **False Positives**: {{ tool.false_positives }}%
- **Execution Time**: {{ tool.execution_time }}s
- **Coverage**: {{ tool.coverage }}%
- **Recommendation**: {{ tool.recommendation }}
{% endfor %}
"""
    
    def generate_comprehensive_report(self, scan_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate all report formats"""
        # Process scan results
        metrics = self._calculate_metrics(scan_results)
        risk_assessment = self._assess_risk(scan_results, metrics)
        compliance_status = self._check_compliance(scan_results)
        
        # Generate different report formats
        reports = {
            'executive_summary': self._generate_executive_summary(
                metrics, risk_assessment, compliance_status
            ),
            'detailed_report': self._generate_detailed_report(scan_results),
            'json_report': json.dumps({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0',
                    'format': 'sarif-2.1.0'
                },
                'metrics': metrics.__dict__,
                'vulnerabilities': scan_results.get('vulnerabilities', []),
                'risk_assessment': risk_assessment,
                'compliance': compliance_status
            }, indent=2),
            'sarif_report': self._generate_sarif_report(scan_results)
        }
        
        return reports
    
    def _calculate_metrics(self, scan_results: Dict[str, Any]) -> SecurityMetrics:
        """Calculate security metrics from scan results"""
        vulnerabilities = scan_results.get('vulnerabilities', [])
        
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return SecurityMetrics(
            total_vulnerabilities=len(vulnerabilities),
            critical_count=severity_counts['CRITICAL'],
            high_count=severity_counts['HIGH'],
            medium_count=severity_counts['MEDIUM'],
            low_count=severity_counts['LOW'],
            tools_used=scan_results.get('tools_used', []),
            scan_duration=scan_results.get('scan_duration', 0),
            coverage_percentage=scan_results.get('coverage', 0),
            false_positive_rate=scan_results.get('false_positive_rate', 0)
        )
    
    def _assess_risk(self, scan_results: Dict[str, Any], metrics: SecurityMetrics) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        # Calculate risk score (0-100)
        risk_score = min(100, (
            metrics.critical_count * 25 +
            metrics.high_count * 15 +
            metrics.medium_count * 5 +
            metrics.low_count * 1
        ))
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'CRITICAL'
        elif risk_score >= 60:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Business impact assessment
        business_impact = {
            'data_breach_probability': min(95, risk_score + metrics.critical_count * 10),
            'service_disruption_risk': min(90, risk_score * 0.8),
            'compliance_violation_risk': min(100, risk_score + (metrics.critical_count * 5)),
            'reputation_damage_potential': min(85, risk_score * 0.9)
        }
        
        return {
            'score': risk_score,
            'level': risk_level,
            'business_impact': business_impact,
            'trending': self._calculate_risk_trend(scan_results),
            'peer_comparison': self._compare_with_industry_standards(risk_score)
        }
    
    def _generate_sarif_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate SARIF 2.1.0 compliant report"""
        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": []
        }
        
        # Group findings by tool
        tools_data = {}
        for vuln in scan_results.get('vulnerabilities', []):
            tool = vuln.get('tool', 'unknown')
            if tool not in tools_data:
                tools_data[tool] = []
            tools_data[tool].append(vuln)
        
        # Create run for each tool
        for tool_name, vulnerabilities in tools_data.items():
            run = {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": "1.0.0",
                        "informationUri": f"https://docs.{tool_name}.com"
                    }
                },
                "results": []
            }
            
            for vuln in vulnerabilities:
                result = {
                    "ruleId": vuln.get('type', 'unknown'),
                    "message": {
                        "text": vuln.get('description', vuln.get('title', 'Security issue detected'))
                    },
                    "level": self._map_severity_to_sarif_level(vuln.get('severity', 'medium')),
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": vuln.get('file_path', 'unknown')
                            },
                            "region": {
                                "startLine": vuln.get('line_number', 1)
                            }
                        }
                    }]
                }
                
                if vuln.get('cwe'):
                    result["properties"] = {
                        "cwe": vuln.get('cwe'),
                        "confidence": vuln.get('confidence', 'medium')
                    }
                
                run["results"].append(result)
            
            sarif_report["runs"].append(run)
        
        return json.dumps(sarif_report, indent=2)
    
    def _map_severity_to_sarif_level(self, severity: str) -> str:
        """Map severity to SARIF level"""
        mapping = {
            'CRITICAL': 'error',
            'HIGH': 'error',
            'MEDIUM': 'warning',
            'LOW': 'note'
        }
        return mapping.get(severity.upper(), 'warning')

# Usage example
report_generator = SecurityReportGenerator()

# Sample scan results
sample_results = {
    'vulnerabilities': [
        {
            'tool': 'bandit',
            'severity': 'HIGH',
            'title': 'SQL Injection vulnerability',
            'description': 'Parameterized query missing',
            'file_path': 'api/users.py',
            'line_number': 45,
            'cwe': 'CWE-89'
        }
    ],
    'tools_used': ['bandit', 'safety', 'trivy'],
    'scan_duration': 120.5,
    'coverage': 85.2
}

reports = report_generator.generate_comprehensive_report(sample_results)
```

**Executive Summary**
```markdown
## Security Assessment Report

**Date**: 2025-07-19
**Severity**: CRITICAL
**Confidence**: 94%

### Summary
- Total Vulnerabilities: 47
- Critical: 8 (17%)
- High: 15 (32%)
- Medium: 18 (38%)
- Low: 6 (13%)

### Critical Findings
1. **SQL Injection** in user search endpoint (api/search.py:45)
2. **Hardcoded AWS credentials** in config.js:12
3. **Outdated dependencies** with known RCE vulnerabilities
4. **Missing authentication** on admin endpoints

### Business Impact
| Risk Category | Probability | Impact | Priority |
|---------------|-------------|--------|----------|
| Data Breach | 85% | Critical | P0 |
| Service Disruption | 60% | High | P1 |
| Compliance Violation | 90% | Critical | P0 |
| Reputation Damage | 70% | High | P1 |

### Immediate Actions Required (Next 24 Hours)
1. **Patch SQL injection vulnerability** (2 hours) - [@dev-team]
2. **Remove and rotate all hardcoded credentials** (1 hour) - [@security-team]
3. **Block admin endpoints** until auth is implemented (30 minutes) - [@ops-team]

### Short-term Actions (Next 30 Days)
1. **Update critical dependencies** (4 hours)
2. **Implement authentication middleware** (6 hours)
3. **Deploy security headers** (2 hours)
4. **Security training for development team** (8 hours)

### Investment Required
- **Immediate fixes**: $5,000 (40 hours @ $125/hr)
- **Security improvements**: $15,000 (120 hours)
- **Training and processes**: $10,000
- **Total**: $30,000

### Compliance Status
- **OWASP Top 10**: 3/10 major issues
- **SOC 2**: Non-compliant (authentication controls)
- **PCI DSS**: Non-compliant (data protection)
- **GDPR**: At risk (data breach potential)
```

**Detailed Findings with Remediation Code**
```json
{
  "scan_metadata": {
    "timestamp": "2025-07-19T10:30:00Z",
    "version": "2.1",
    "tools_used": ["bandit", "safety", "trivy", "semgrep", "eslint-security"],
    "scan_duration_seconds": 127,
    "coverage_percentage": 94.2,
    "false_positive_rate": 3.1
  },
  "vulnerabilities": [
    {
      "id": "VULN-001",
      "type": "SQL Injection",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "cwe": "CWE-89",
      "owasp_category": "A03:2021-Injection",
      "tool": "semgrep",
      "confidence": "high",
      "location": {
        "file": "api/search.js",
        "line": 45,
        "column": 12,
        "code_snippet": "db.query(`SELECT * FROM users WHERE name LIKE '%${req.query.search}%'`)",
        "function": "searchUsers"
      },
      "impact": {
        "description": "Complete database compromise, data exfiltration, potential RCE",
        "business_impact": "Critical - customer data exposure, regulatory violations",
        "affected_users": "All users with search functionality access"
      },
      "remediation": {
        "effort_hours": 2,
        "priority": "P0",
        "description": "Replace string concatenation with parameterized queries",
        "fixed_code": "db.query('SELECT * FROM users WHERE name LIKE ?', [`%${req.query.search}%`])",
        "testing_required": "Unit tests for search functionality",
        "deployment_notes": "No breaking changes, safe to deploy immediately"
      },
      "references": [
        {
          "title": "OWASP SQL Injection Prevention",
          "url": "https://owasp.org/www-community/attacks/SQL_Injection"
        },
        {
          "title": "Node.js Parameterized Queries",
          "url": "https://nodejs.org/en/docs/guides/security/"
        }
      ],
      "exploitability": {
        "ease_of_exploitation": "Very Easy",
        "attack_vector": "Remote",
        "authentication_required": false,
        "user_interaction": false
      }
    },
    {
      "id": "VULN-002",
      "type": "Hardcoded Secrets",
      "severity": "CRITICAL",
      "cvss_score": 9.1,
      "cwe": "CWE-798",
      "tool": "trufflehog",
      "confidence": "verified",
      "location": {
        "file": "{{PATH_CONFIG}}/database.js",
        "line": 12,
        "code_snippet": "const password = 'MyS3cr3tP@ssw0rd123!'"
      },
      "impact": {
        "description": "Database credentials exposure, unauthorized access",
        "business_impact": "Critical - full database access, data breach potential"
      },
      "remediation": {
        "effort_hours": 1,
        "priority": "P0",
        "immediate_actions": [
          "Rotate database password immediately",
          "Remove hardcoded credential from code",
          "Implement environment variable loading"
        ],
        "fixed_code": "const password = process.env.DATABASE_PASSWORD || throwError('Missing DATABASE_PASSWORD')",
        "additional_steps": [
          "Add .env to .gitignore",
          "Update deployment scripts to use secrets management",
          "Scan git history for credential exposure"
        ]
      }
    },
    {
      "id": "VULN-003",
      "type": "Vulnerable Dependency",
      "severity": "HIGH",
      "cvss_score": 8.5,
      "cve": "CVE-2024-1234",
      "tool": "npm-audit",
      "location": {
        "file": "package.json",
        "dependency": "express",
        "version": "4.17.1",
        "vulnerable_path": "express > body-parser > raw-body"
      },
      "impact": {
        "description": "Remote code execution via malformed request body",
        "affected_endpoints": ["/api/upload", "/api/webhook"]
      },
      "remediation": {
        "effort_hours": 0.5,
        "priority": "P1",
        "fixed_version": "4.18.2",
        "update_command": "npm install express@4.18.2",
        "breaking_changes": false,
        "testing_required": "Regression testing for API endpoints"
      }
    }
  ],
  "summary": {
    "total_vulnerabilities": 47,
    "by_severity": {
      "critical": 8,
      "high": 15,
      "medium": 18,
      "low": 6
    },
    "by_category": {
      "injection": 12,
      "broken_auth": 8,
      "sensitive_data": 6,
      "xml_entities": 2,
      "broken_access_control": 5,
      "security_misconfig": 9,
      "xss": 3,
      "insecure_deserialization": 1,
      "vulnerable_components": 15,
      "insufficient_logging": 4
    },
    "remediation_timeline": {
      "immediate_p0": 9,
      "urgent_p1": 18,
      "medium_p2": 15,
      "low_p3": 5
    },
    "total_effort_hours": 47.5,
    "estimated_cost": 5938,
    "risk_score": 89
  },
  "compliance_assessment": {
    "owasp_top_10_2021": {
      "a01_broken_access_control": "FAIL",
      "a02_cryptographic_failures": "PASS",
      "a03_injection": "FAIL",
      "a04_insecure_design": "WARNING",
      "a05_security_misconfiguration": "FAIL",
      "a06_vulnerable_components": "FAIL",
      "a07_identification_failures": "FAIL",
      "a08_software_integrity_failures": "PASS",
      "a09_logging_failures": "WARNING",
      "a10_ssrf": "PASS"
    },
    "frameworks": {
      "nist_cybersecurity": 67,
      "iso_27001": 71,
      "pci_dss": 45,
      "sox_compliance": 78
    }
  }
}
```

### 2. Cross-Command Integration

### Complete Security-First Development Workflow

**Secure API Development Pipeline**
```bash
# 1. Generate secure API scaffolding
/api-scaffold
framework: "fastapi"
security_features: ["jwt_auth", "rate_limiting", "input_validation", "cors"]
database: "postgresql"

# 2. Run comprehensive security scan
/security-scan
scan_types: ["sast", "dependency", "secrets", "container", "iac"]
autofix: true
generate_report: true

# 3. Generate security-aware tests
/test-harness
test_types: ["unit", "security", "penetration"]
security_frameworks: ["bandit", "safety", "owasp-zap"]

# 4. Optimize containers with security hardening
/docker-optimize
security_hardening: true
vulnerability_scanning: true
minimal_base_images: true
```

**Integrated Security Configuration**
```python
# security-config.py - Shared across all commands
class IntegratedSecurityConfig:
    def __init__(self):
        self.api_security = self.load_api_security_config()    # From /api-scaffold
        self.scan_config = self.load_scan_config()             # From /security-scan
        self.test_security = self.load_test_security_config()  # From /test-harness
        self.container_security = self.load_container_config() # From /docker-optimize
        
    def generate_security_middleware(self):
        """Generate security middleware based on API scaffold config"""
        middleware = []
        
        if self.api_security.get('rate_limiting'):
            middleware.append({
                'type': 'rate_limiting',
                'config': {
                    'requests_per_minute': 100,
                    'burst_size': 10,
                    'key_func': 'lambda request: request.client.host'
                }
            })
        
        if self.api_security.get('jwt_auth'):
            middleware.append({
                'type': 'jwt_auth',
                'config': {
                    'secret_key': '${JWT_SECRET_KEY}',
                    'algorithm': 'HS256',
                    'token_expiry': 3600
                }
            })
        
        return middleware
    
    def generate_security_tests(self):
        """Generate security tests based on scan findings"""
        test_cases = []
        
        # SQL Injection tests based on API endpoints
        api_endpoints = self.api_security.get('endpoints', [])
        for endpoint in api_endpoints:
            if endpoint.get('accepts_input'):
                test_cases.append({
                    'type': 'sql_injection',
                    'endpoint': endpoint['path'],
                    'payloads': self.get_sql_injection_payloads()
                })
        
        # Authentication bypass tests
        if self.api_security.get('jwt_auth'):
            test_cases.append({
                'type': 'auth_bypass',
                'scenarios': [
                    'invalid_token',
                    'expired_token',
                    'malformed_token',
                    'no_token'
                ]
            })
        
        return test_cases
    
    def generate_container_security_policies(self):
        """Generate container security policies"""
        policies = {
            'dockerfile_security': {
                'non_root_user': True,
                'minimal_layers': True,
                'security_updates': True,
                'no_secrets_in_layers': True
            },
            'runtime_security': {
                'read_only_filesystem': True,
                'no_new_privileges': True,
                'drop_capabilities': ['ALL'],
                'add_capabilities': ['NET_BIND_SERVICE'] if self.api_security.get('bind_privileged_ports') else []
            }
        }
        return policies
```

**API Security Integration**
```python
# Generated secure API endpoint with integrated security
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import jwt
from datetime import datetime, timedelta

# Security configuration from /security-scan
security_config = IntegratedSecurityConfig()

# Rate limiting from security scan recommendations
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# JWT authentication from security scan requirements
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT verification with security scan compliance"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            security_config.jwt_secret, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Secure endpoint with integrated protections
@app.post("/api/v1/users/")
@limiter.limit("10/minute")  # Rate limiting from security scan
async def create_user(
    request: Request,
    user_data: UserCreateSchema,  # Input validation from security scan
    current_user: dict = Depends(verify_token)  # Authentication
):
    """
    Secure user creation endpoint with integrated security controls
    Security features applied:
    - Rate limiting (10 requests/minute)
    - JWT authentication required
    - Input validation via Pydantic
    - SQL injection prevention via ORM
    - XSS prevention via output encoding
    """
    # Additional security validation from scan results
    if not validate_user_input(user_data):
        raise HTTPException(status_code=400, detail="Invalid input data")
    
    # Create user with security logging
    try:
        user = await user_service.create_user(user_data)
        security_logger.log_user_creation(current_user['sub'], user.id)
        return user
    except Exception as e:
        security_logger.log_error("user_creation_failed", str(e))
        raise HTTPException(status_code=500, detail="User creation failed")
```

**Database Security Integration**
```python
# Database security configuration from /db-migrate and /security-scan
class SecureDatabaseConfig:
    def __init__(self):
        self.migration_config = self.load_migration_config()  # From /db-migrate
        self.security_requirements = self.load_security_scan_results()
        
    def generate_secure_migrations(self):
        """Generate database migrations with security controls"""
        migrations = []
        
        # User table with security controls
        migrations.append({
            'operation': 'create_table',
            'table': 'users',
            'columns': [
                {'name': 'id', 'type': 'UUID', 'primary_key': True},
                {'name': 'email', 'type': 'VARCHAR(255)', 'unique': True, 'encrypted': True},
                {'name': 'password_hash', 'type': 'VARCHAR(255)', 'not_null': True},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'default': 'NOW()'},
                {'name': 'last_login', 'type': 'TIMESTAMP'},
                {'name': 'failed_login_attempts', 'type': 'INTEGER', 'default': 0},
                {'name': 'locked_until', 'type': 'TIMESTAMP', 'nullable': True}
            ],
            'security_features': {
                'row_level_security': True,
                'audit_logging': True,
                'field_encryption': ['email'],
                'password_policy': {
                    'min_length': 12,
                    'require_special_chars': True,
                    'require_numbers': True,
                    'expire_days': 90
                }
            }
        })
        
        # Security audit log table
        migrations.append({
            'operation': 'create_table',
            'table': 'security_audit_log',
            'columns': [
                {'name': 'id', 'type': 'UUID', 'primary_key': True},
                {'name': 'user_id', 'type': 'UUID', 'foreign_key': 'users.id'},
                {'name': 'action', 'type': 'VARCHAR(100)', 'not_null': True},
                {'name': 'ip_address', 'type': 'INET', 'not_null': True},
                {'name': 'user_agent', 'type': 'TEXT'},
                {'name': 'timestamp', 'type': 'TIMESTAMP', 'default': 'NOW()'},
                {'name': 'success', 'type': 'BOOLEAN', 'not_null': True},
                {'name': 'details', 'type': 'JSONB'}
            ],
            'indexes': [
                {'name': 'idx_audit_user_timestamp', 'columns': ['user_id', 'timestamp']},
                {'name': 'idx_audit_action_timestamp', 'columns': ['action', 'timestamp']}
            ]
        })
        
        return migrations
```

**Monitoring and Alerting Integration**
```python
# security_monitoring.py - Integrated with all commands
import logging
from datetime import datetime
from typing import Dict, Any
import json

class IntegratedSecurityMonitor:
    """Security monitoring that integrates with all command outputs"""
    
    def __init__(self):
        self.api_endpoints = self.load_api_endpoints()      # From /api-scaffold
        self.container_metrics = self.load_container_config() # From /docker-optimize
        self.k8s_security = self.load_k8s_security()        # From /k8s-manifest
        
    def monitor_api_security(self):
        """Monitor API security events"""
        security_events = []
        
        # Monitor authentication failures
        auth_failures = self.get_auth_failure_rate()
        if auth_failures > 10:  # More than 10 failures per minute
            security_events.append({
                'type': 'AUTH_FAILURE_SPIKE',
                'severity': 'HIGH',
                'details': f'Authentication failure rate: {auth_failures}/min',
                'recommended_action': 'Check for brute force attacks'
            })
        
        # Monitor rate limiting violations
        rate_limit_violations = self.get_rate_limit_violations()
        if rate_limit_violations:
            security_events.append({
                'type': 'RATE_LIMIT_VIOLATION',
                'severity': 'MEDIUM',
                'details': f'Rate limit violations: {len(rate_limit_violations)}',
                'ips': [v['ip'] for v in rate_limit_violations],
                'recommended_action': 'Consider IP blocking or CAPTCHA'
            })
        
        return security_events
    
    def monitor_container_security(self):
        """Monitor container security events"""
        container_events = []
        
        # Check for privilege escalation attempts
        privilege_events = self.check_privilege_escalation()
        if privilege_events:
            container_events.append({
                'type': 'PRIVILEGE_ESCALATION',
                'severity': 'CRITICAL',
                'containers': privilege_events,
                'recommended_action': 'Immediate investigation required'
            })
        
        # Check for filesystem violations
        readonly_violations = self.check_readonly_violations()
        if readonly_violations:
            container_events.append({
                'type': 'READONLY_VIOLATION',
                'severity': 'HIGH',
                'violations': readonly_violations,
                'recommended_action': 'Review container security policies'
            })
        
        return container_events
    
    def generate_security_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive security dashboard"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'api_security': self.monitor_api_security(),
            'container_security': self.monitor_container_security(),
            'scan_results': self.get_latest_scan_results(),
            'test_results': self.get_security_test_results(),
            'compliance_status': self.check_compliance_status(),
            'recommendations': self.generate_recommendations()
        }
```

This integrated approach ensures that security is built into every aspect of the application lifecycle, from development through deployment and monitoring.

## Related Templates

- **`backend/security-scan.md`** -- Backend SAST, API security, dependency scanning, secret detection, and backend remediation patterns
- **`frontend/security-scan.md`** -- Frontend XSS/CSRF/clickjacking detection, CSP validation, security headers, and client-side remediation
- **`cloud/security-scan.md`** -- IaC scanning (Checkov, tfsec, kube-score), container security, CI/CD pipelines, and infrastructure hardening

## Output Format

1. **Executive Security Report**: Business-focused risk assessment
2. **Detailed Technical Findings**: Code-level vulnerabilities with fixes
3. **SARIF Compliance Report**: Industry-standard security report format
4. **Compliance Assessment**: OWASP, NIST, ISO 27001 compliance mapping
5. **Business Impact Analysis**: Risk quantification and cost estimates
6. **Cross-Command Integration**: Orchestrated security across all templates

**Key Features**:
- Multi-tool integration: Aggregates results from backend, frontend, and cloud scans
- Business context: Risk scoring with financial impact estimates
- Compliance-focused: Built-in OWASP Top 10, CWE, and regulatory mappings
- Actionable insights: Specific remediation code and deployment guidance
- Cross-command orchestration: Coordinates security across all domain templates

Focus on actionable remediation that can be implemented immediately while maintaining application functionality.
