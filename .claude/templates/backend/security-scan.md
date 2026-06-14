---
model: claude-sonnet-4-0
description: Backend Security Scanning
complexity: advanced
priority: critical
tags: [security, backend, api, auth]
depends_on: []
chains_to: []
skip_if: []
version: 1.0.0
---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Backend Security Scanning

You are a security expert specializing in backend application security, vulnerability assessment, and secure coding practices. Perform comprehensive backend security audits to identify vulnerabilities, provide remediation guidance, and implement security best practices.

## Context
The user needs a thorough backend security analysis covering SAST, dependency scanning, API security, secret detection, and secure coding patterns. Focus on OWASP Top 10 backend-relevant categories, dependency vulnerabilities, and code-level security issues with actionable remediation steps.

## Requirements
$ARGUMENTS

## Instructions

### 1. Security Scanning Tool Selection (Backend)

Choose appropriate backend security scanning tools based on your technology stack:

**SAST Tools and Code Vulnerability Scanners**
```python
security_tools = {
    'python': {
        'sast': {
            'bandit': {
                'strengths': ['Built for Python', 'Fast', 'Good defaults', 'AST-based'],
                'best_for': ['Python codebases', 'CI/CD pipelines', 'Quick scans'],
                'command': 'bandit -r . -f json -o bandit-report.json',
                'config_file': '.bandit'
            },
            'semgrep': {
                'strengths': ['Multi-language', 'Custom rules', 'Low false positives'],
                'best_for': ['Complex projects', 'Custom security patterns', 'Enterprise'],
                'command': 'semgrep --config=auto --json --output=semgrep-report.json',
                'config_file': '.semgrep.yml'
            }
        },
        'dependency_scan': {
            'safety': {
                'command': 'safety check --json --output safety-report.json',
                'database': 'PyUp.io vulnerability database',
                'best_for': 'Python package vulnerabilities'
            },
            'pip_audit': {
                'command': 'pip-audit --format=json --output=pip-audit-report.json',
                'database': 'OSV database',
                'best_for': 'Comprehensive Python vulnerability scanning'
            }
        }
    },
    
    'javascript': {
        'sast': {
            'eslint_security': {
                'command': 'eslint . --ext .js,.jsx,.ts,.tsx --format json > eslint-security.json',
                'plugins': ['@eslint/plugin-security', 'eslint-plugin-no-secrets'],
                'best_for': 'JavaScript/TypeScript security linting'
            },
            'sonarjs': {
                'command': 'sonar-scanner -Dsonar.projectKey=myproject',
                'best_for': 'Comprehensive code quality and security',
                'features': ['Vulnerability detection', 'Code smells', 'Technical debt']
            }
        },
        'dependency_scan': {
            'npm_audit': {
                'command': 'npm audit --json > npm-audit-report.json',
                'fix': 'npm audit fix',
                'best_for': 'NPM package vulnerabilities'
            },
            'yarn_audit': {
                'command': 'yarn audit --json > yarn-audit-report.json',
                'best_for': 'Yarn package vulnerabilities'
            },
            'snyk': {
                'command': 'snyk test --json > snyk-report.json',
                'fix': 'snyk wizard',
                'best_for': 'Comprehensive vulnerability management'
            }
        }
    },
    
    'secrets': {
        'truffleHog': {
            'command': 'trufflehog git file://. --json > trufflehog-report.json',
            'strengths': ['Git history scanning', 'High accuracy', 'Custom regex'],
            'best_for': 'Secret detection in git repositories'
        },
        'gitleaks': {
            'command': 'gitleaks detect --report-format json --report-path gitleaks-report.json',
            'strengths': ['Fast', 'Configurable', 'Pre-commit hooks'],
            'best_for': 'Real-time secret detection'
        },
        'detect_secrets': {
            'command': 'detect-secrets scan --all-files . > .secrets.baseline',
            'strengths': ['Baseline management', 'False positive reduction'],
            'best_for': 'Enterprise secret management'
        }
    }
}
```

**Multi-Tool Security Scanner**
```python
import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VulnerabilityFinding:
    tool: str
    severity: str
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    cve: str
    cwe: str
    remediation: str
    confidence: str

class SecurityScanner:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.findings = []
        self.scan_results = {}
        
    def detect_project_type(self) -> List[str]:
        """Detect project technologies to choose appropriate scanners"""
        technologies = []
        
        # Python
        if (self.project_path / 'requirements.txt').exists() or \
           (self.project_path / 'setup.py').exists() or \
           (self.project_path / 'pyproject.toml').exists():
            technologies.append('python')
            
        # JavaScript/Node.js
        if (self.project_path / 'package.json').exists():
            technologies.append('javascript')
            
        # Go
        if (self.project_path / 'go.mod').exists():
            technologies.append('golang')
            
        return technologies
    
    def run_comprehensive_scan(self) -> Dict[str, Any]:
        """Run all applicable security scanners"""
        technologies = self.detect_project_type()
        
        scan_plan = {
            'timestamp': datetime.now().isoformat(),
            'technologies': technologies,
            'scanners_used': [],
            'findings': []
        }
        
        # Always run secret detection
        self.run_secret_scan()
        scan_plan['scanners_used'].append('secret_detection')
        
        # Technology-specific scans
        if 'python' in technologies:
            self.run_python_scans()
            scan_plan['scanners_used'].extend(['bandit', 'safety', 'pip_audit'])
            
        if 'javascript' in technologies:
            self.run_javascript_scans()
            scan_plan['scanners_used'].extend(['eslint_security', 'npm_audit'])
            
        # Generate unified report
        scan_plan['findings'] = self.findings
        scan_plan['summary'] = self.generate_summary()
        
        return scan_plan
    
    def run_secret_scan(self):
        """Run secret detection tools"""
        try:
            # TruffleHog
            result = subprocess.run([
                'trufflehog', 'filesystem', str(self.project_path),
                '--json', '--no-update'
            ], capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        finding = json.loads(line)
                        self.findings.append(VulnerabilityFinding(
                            tool='trufflehog',
                            severity='CRITICAL',
                            category='secrets',
                            title=f"Secret detected: {finding.get('DetectorName', 'Unknown')}",
                            description=finding.get('Raw', ''),
                            file_path=finding.get('SourceMetadata', {}).get('Data', {}).get('Filesystem', {}).get('file', ''),
                            line_number=finding.get('SourceMetadata', {}).get('Data', {}).get('Filesystem', {}).get('line', 0),
                            cve='',
                            cwe='CWE-798',
                            remediation='Remove secret and rotate credentials',
                            confidence=str(finding.get('Verified', False))
                        ))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("TruffleHog not available or scan failed")
            
        try:
            # GitLeaks
            result = subprocess.run([
                'gitleaks', 'detect', '--source', str(self.project_path),
                '--report-format', 'json', '--no-git'
            ], capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                findings = json.loads(result.stdout)
                for finding in findings:
                    self.findings.append(VulnerabilityFinding(
                        tool='gitleaks',
                        severity='HIGH',
                        category='secrets',
                        title=f"Secret pattern: {finding.get('RuleID', 'Unknown')}",
                        description=finding.get('Description', ''),
                        file_path=finding.get('File', ''),
                        line_number=finding.get('StartLine', 0),
                        cve='',
                        cwe='CWE-798',
                        remediation='Remove secret and add to .gitignore',
                        confidence='high'
                    ))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("GitLeaks not available or scan failed")
    
    def run_python_scans(self):
        """Run Python-specific security scanners"""
        # Bandit
        try:
            result = subprocess.run([
                'bandit', '-r', str(self.project_path),
                '-f', 'json', '--severity-level', 'medium'
            ], capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                for result_item in bandit_results.get('results', []):
                    self.findings.append(VulnerabilityFinding(
                        tool='bandit',
                        severity=result_item.get('issue_severity', 'MEDIUM'),
                        category='sast',
                        title=result_item.get('test_name', ''),
                        description=result_item.get('issue_text', ''),
                        file_path=result_item.get('filename', ''),
                        line_number=result_item.get('line_number', 0),
                        cve='',
                        cwe=result_item.get('test_id', ''),
                        remediation=result_item.get('more_info', ''),
                        confidence=result_item.get('issue_confidence', 'MEDIUM')
                    ))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("Bandit not available or scan failed")
        
        # Safety
        try:
            result = subprocess.run([
                'safety', 'check', '--json'
            ], capture_output=True, text=True, timeout=300, cwd=self.project_path)
            
            if result.stdout:
                safety_results = json.loads(result.stdout)
                for vuln in safety_results:
                    self.findings.append(VulnerabilityFinding(
                        tool='safety',
                        severity='HIGH',
                        category='dependencies',
                        title=f"Vulnerable package: {vuln.get('package_name', '')}",
                        description=vuln.get('advisory', ''),
                        file_path='requirements.txt',
                        line_number=0,
                        cve=vuln.get('cve', ''),
                        cwe='',
                        remediation=f"Update to version {vuln.get('analyzed_version', 'latest')}",
                        confidence='high'
                    ))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("Safety not available or scan failed")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        category_counts = {}
        
        for finding in self.findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1
        
        return {
            'total_findings': len(self.findings),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'risk_score': self.calculate_risk_score(severity_counts)
        }
    
    def calculate_risk_score(self, severity_counts: Dict[str, int]) -> int:
        """Calculate overall risk score (0-100)"""
        weights = {'CRITICAL': 10, 'HIGH': 7, 'MEDIUM': 4, 'LOW': 1}
        total_score = sum(weights[severity] * count for severity, count in severity_counts.items())
        max_possible = 100  # Arbitrary ceiling
        return min(100, int((total_score / max_possible) * 100))
```

**SAST (Static Application Security Testing)**
```python
# Enhanced code vulnerability patterns with tool-specific implementations
security_rules = {
    "sql_injection": {
        "patterns": [
            r"query\s*\(\s*[\"'].*\+.*[\"']\s*\)",
            r"execute\s*\(\s*[\"'].*%[s|d].*[\"']\s*%",
            r"f[\"'].*SELECT.*{.*}.*FROM"
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-89",
        "fix": "Use parameterized queries or prepared statements"
    
    "hardcoded_secrets": {
        "patterns": [
            r"(?i)(api[_-]?key|apikey|secret|password)\s*[:=]\s*[\"'][^\"']{8,}[\"']",
            r"(?i)bearer\s+[a-zA-Z0-9\-\._~\+\/]{20,}",
            r"(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret)\s*[:=]",
            r"private[_-]?key\s*[:=]\s*[\"'][^\"']+[\"']"
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-798",
        "fix": "Use environment variables or secure key management service"
    },
    
    "path_traversal": {
        "patterns": [
            r"\.\.\/",
            r"readFile\s*\([^\"']*\+",
            r"include\s*\([^\"']*\$",
            r"require\s*\([^\"']*\+"
        ],
        "severity": "HIGH",
        "cwe": "CWE-22",
        "fix": "Validate and sanitize file paths"
    },
    
    "insecure_random": {
        "patterns": [
            r"Math\.random\(\)",
            r"rand\(\)",
            r"mt_rand\(\)"
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-330",
        "fix": "Use cryptographically secure random functions"
    }
}

def scan_code_vulnerabilities(file_path, content):
    """
    Enhanced code vulnerability scanning with framework-specific patterns
    """
    vulnerabilities = []
    
    for vuln_type, rule in security_rules.items():
        for pattern in rule['patterns']:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                vulnerabilities.append({
                    'type': vuln_type,
                    'severity': rule['severity'],
                    'file': file_path,
                    'line': line_num,
                    'code': match.group(0),
                    'cwe': rule['cwe'],
                    'fix': rule['fix'],
                    'confidence': rule.get('confidence', 'medium'),
                    'owasp_category': rule.get('owasp', 'A03:2021-Injection')
                })
    
    return vulnerabilities

# Framework-specific security patterns
framework_security_patterns = {
    'django': {
        'csrf_exempt': {
            'pattern': r'@csrf_exempt',
            'severity': 'HIGH',
            'description': 'CSRF protection disabled',
            'fix': 'Remove @csrf_exempt decorator and implement proper CSRF protection'
        },
        'raw_sql': {
            'pattern': r'\.raw\(["\'][^"\']\*["\']\)',
            'severity': 'HIGH',
            'description': 'Raw SQL query detected',
            'fix': 'Use Django ORM or parameterized queries'
        },
        'eval_usage': {
            'pattern': r'eval\(',
            'severity': 'CRITICAL',
            'description': 'Code evaluation detected',
            'fix': 'Remove eval() usage and use safe alternatives'
        }
    },
    
    'flask': {
        'debug_mode': {
            'pattern': r'debug\s*=\s*True',
            'severity': 'MEDIUM',
            'description': 'Debug mode enabled in production',
            'fix': 'Set debug=False in production'
        },
        'render_template_string': {
            'pattern': r'render_template_string\([^)]*\+',
            'severity': 'HIGH',
            'description': 'Template injection vulnerability',
            'fix': 'Use render_template with static templates'
        }
    },
    
    'express': {
        'missing_helmet': {
            'pattern': r'express\(\)',
            'negative_pattern': r'helmet\(\)',
            'severity': 'MEDIUM',
            'description': 'Security headers middleware missing',
            'fix': 'Add helmet() middleware for security headers'
        },
        'cors_wildcard': {
            'pattern': r'origin:\s*["\']\*["\']',
            'severity': 'HIGH',
            'description': 'CORS configured with wildcard origin',
            'fix': 'Specify exact allowed origins'
        }
    }
}

def scan_framework_vulnerabilities(framework, file_path, content):
    """Scan for framework-specific security issues"""
    vulnerabilities = []
    
    if framework not in framework_security_patterns:
        return vulnerabilities
    
    patterns = framework_security_patterns[framework]
    
    for vuln_type, rule in patterns.items():
        matches = re.finditer(rule['pattern'], content, re.MULTILINE)
        
        # Check for negative patterns (e.g., missing security middleware)
        if 'negative_pattern' in rule:
            if not re.search(rule['negative_pattern'], content):
                vulnerabilities.append({
                    'type': f'{framework}_{vuln_type}',
                    'severity': rule['severity'],
                    'file': file_path,
                    'description': rule['description'],
                    'fix': rule['fix'],
                    'framework': framework
                })
        else:
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                vulnerabilities.append({
                    'type': f'{framework}_{vuln_type}',
                    'severity': rule['severity'],
                    'file': file_path,
                    'line': line_num,
                    'code': match.group(0),
                    'description': rule['description'],
                    'fix': rule['fix'],
                    'framework': framework
                })
    
    return vulnerabilities
```

**Advanced Dependency Vulnerability Scanning**
```python
import subprocess
import json
import requests
from typing import Dict, List, Any
from datetime import datetime, timedelta

class DependencyScanner:
    def __init__(self):
        self.vulnerability_databases = {
            'osv': 'https://api.osv.dev/v1/query',
            'snyk': 'https://api.snyk.io/v1/test',
            'github': 'https://api.github.com/advisories'
        }
    
    def scan_all_ecosystems(self, project_path: str) -> Dict[str, Any]:
        """Comprehensive dependency scanning across all package managers"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'ecosystems': {},
            'summary': {'total_vulnerabilities': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        }
        
        # Detect and scan each ecosystem
        ecosystems = self.detect_ecosystems(project_path)
        
        for ecosystem in ecosystems:
            results['ecosystems'][ecosystem] = self.scan_ecosystem(ecosystem, project_path)
            self.update_summary(results['summary'], results['ecosystems'][ecosystem])
        
        return results
    
    def detect_ecosystems(self, project_path: str) -> List[str]:
        """Detect package managers and dependency files"""
        ecosystems = []
        
        ecosystem_files = {
            'npm': ['package.json', 'package-lock.json', 'yarn.lock'],
            'pip': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'gem': ['Gemfile', 'Gemfile.lock'],
            'composer': ['composer.json', 'composer.lock'],
            'nuget': ['*.csproj', 'packages.config'],
            'go': ['go.mod', 'go.sum'],
            'rust': ['Cargo.toml', 'Cargo.lock']
        }
        
        for ecosystem, files in ecosystem_files.items():
            if any(Path(project_path).glob(f) for f in files):
                ecosystems.append(ecosystem)
        
        return ecosystems
    
    def scan_npm_dependencies(self, project_path: str) -> Dict[str, Any]:
        """Scan NPM dependencies using multiple tools"""
        results = {
            'tool_results': {},
            'vulnerabilities': [],
            'total_packages': 0,
            'outdated_packages': []
        }
        
        # NPM Audit
        try:
            npm_result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if npm_result.stdout:
                audit_data = json.loads(npm_result.stdout)
                results['tool_results']['npm_audit'] = audit_data
                
                for vuln_id, vuln in audit_data.get('vulnerabilities', {}).items():
                    results['vulnerabilities'].append({
                        'id': vuln_id,
                        'severity': vuln.get('severity', 'unknown'),
                        'title': vuln.get('title', ''),
                        'package': vuln.get('name', ''),
                        'version': vuln.get('range', ''),
                        'cwe': vuln.get('cwe', []),
                        'cve': vuln.get('cves', []),
                        'fixed_in': vuln.get('fixAvailable', ''),
                        'source': 'npm_audit'
                    })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            results['tool_results']['npm_audit'] = {'error': 'Failed to run npm audit'}
        
        # Snyk scan (if available)
        try:
            snyk_result = subprocess.run(
                ['snyk', 'test', '--json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if snyk_result.stdout:
                snyk_data = json.loads(snyk_result.stdout)
                results['tool_results']['snyk'] = snyk_data
                
                for vuln in snyk_data.get('vulnerabilities', []):
                    results['vulnerabilities'].append({
                        'id': vuln.get('id', ''),
                        'severity': vuln.get('severity', 'unknown'),
                        'title': vuln.get('title', ''),
                        'package': vuln.get('packageName', ''),
                        'version': vuln.get('version', ''),
                        'cve': vuln.get('identifiers', {}).get('CVE', []),
                        'cwe': vuln.get('identifiers', {}).get('CWE', []),
                        'upgrade_path': vuln.get('upgradePath', []),
                        'source': 'snyk'
                    })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            results['tool_results']['snyk'] = {'error': 'Snyk not available or failed'}
        
        return results
    
    def scan_python_dependencies(self, project_path: str) -> Dict[str, Any]:
        """Comprehensive Python dependency scanning"""
        results = {
            'tool_results': {},
            'vulnerabilities': [],
            'license_issues': []
        }
        
        # Safety scan
        try:
            safety_result = subprocess.run(
                ['safety', 'check', '--json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if safety_result.stdout:
                safety_data = json.loads(safety_result.stdout)
                results['tool_results']['safety'] = safety_data
                
                for vuln in safety_data:
                    results['vulnerabilities'].append({
                        'package': vuln.get('package_name', ''),
                        'version': vuln.get('analyzed_version', ''),
                        'vulnerability_id': vuln.get('vulnerability_id', ''),
                        'advisory': vuln.get('advisory', ''),
                        'cve': vuln.get('cve', ''),
                        'severity': self.map_safety_severity(vuln.get('vulnerability_id', '')),
                        'source': 'safety'
                    })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            results['tool_results']['safety'] = {'error': 'Safety scan failed'}
        
        # pip-audit scan
        try:
            pip_audit_result = subprocess.run(
                ['pip-audit', '--format=json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if pip_audit_result.stdout:
                pip_audit_data = json.loads(pip_audit_result.stdout)
                results['tool_results']['pip_audit'] = pip_audit_data
                
                for vuln in pip_audit_data.get('vulnerabilities', []):
                    results['vulnerabilities'].append({
                        'package': vuln.get('package', ''),
                        'version': vuln.get('version', ''),
                        'vulnerability_id': vuln.get('id', ''),
                        'description': vuln.get('description', ''),
                        'aliases': vuln.get('aliases', []),
                        'fix_versions': vuln.get('fix_versions', []),
                        'source': 'pip_audit'
                    })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            results['tool_results']['pip_audit'] = {'error': 'pip-audit not available'}
        
        return results
    
    def generate_remediation_plan(self, vulnerabilities: List[Dict]) -> Dict[str, Any]:
        """Generate prioritized remediation plan"""
        plan = {
            'immediate_actions': [],
            'short_term': [],
            'long_term': [],
            'automation_scripts': {}
        }
        
        # Sort by severity
        critical_high = [v for v in vulnerabilities if v.get('severity', '').upper() in ['CRITICAL', 'HIGH']]
        medium = [v for v in vulnerabilities if v.get('severity', '').upper() == 'MEDIUM']
        low = [v for v in vulnerabilities if v.get('severity', '').upper() == 'LOW']
        
        # Immediate actions for critical/high
        for vuln in critical_high:
            plan['immediate_actions'].append({
                'package': vuln.get('package', ''),
                'current_version': vuln.get('version', ''),
                'fixed_version': vuln.get('fixed_in', vuln.get('fix_versions', ['latest'])[0] if vuln.get('fix_versions') else 'latest'),
                'action': f"Update {vuln.get('package', '')} to {vuln.get('fixed_in', 'latest')}",
                'priority': 1,
                'effort': 'Low'
            })
        
        # Auto-update script
        plan['automation_scripts']['npm_auto_update'] = """
#!/bin/bash
# Automated npm dependency updates
npm audit fix --force
npm update
npm audit
"""
        
        plan['automation_scripts']['pip_auto_update'] = """
#!/bin/bash
# Automated Python dependency updates
pip install --upgrade pip
pip-audit --fix
safety check
"""
        
        return plan

# Multi-ecosystem scanner
class UniversalDependencyScanner:
    def __init__(self):
        self.scanners = {
            'python': self.scan_python_dependencies,
            'javascript': self.scan_npm_dependencies,
            'java': self.scan_java_dependencies,
            'go': self.scan_go_dependencies,
            'rust': self.scan_rust_dependencies,
        }
    
    def scan_python_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Enhanced Python dependency scanning with multiple tools
        """
        results = {
            'tools_used': ['safety', 'pip-audit', 'bandit'],
            'vulnerabilities': [],
            'license_compliance': [],
            'outdated_packages': []
        }
        
        # Safety check
        try:
            safety_cmd = ['safety', 'check', '--json', '--full-report']
            result = subprocess.run(safety_cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data:
                    results['vulnerabilities'].append({
                        'tool': 'safety',
                        'package': vuln.get('package_name'),
                        'version': vuln.get('analyzed_version'),
                        'vulnerability_id': vuln.get('vulnerability_id'),
                        'severity': self._map_safety_severity(vuln.get('vulnerability_id')),
                        'advisory': vuln.get('advisory'),
                        'cve': vuln.get('cve'),
                        'remediation': f"Update to {vuln.get('fixed_version', 'latest version')}"
                    })
        except Exception as e:
            results['safety_error'] = str(e)
        
        # pip-audit
        try:
            pip_audit_cmd = ['pip-audit', '--format=json', '--desc']
            result = subprocess.run(pip_audit_cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                pip_audit_data = json.loads(result.stdout)
                for vuln in pip_audit_data.get('vulnerabilities', []):
                    results['vulnerabilities'].append({
                        'tool': 'pip-audit',
                        'package': vuln.get('package'),
                        'version': vuln.get('version'),
                        'vulnerability_id': vuln.get('id'),
                        'severity': self._calculate_severity_from_cvss(vuln.get('fix_versions', [])),
                        'description': vuln.get('description'),
                        'aliases': vuln.get('aliases', []),
                        'fix_versions': vuln.get('fix_versions', []),
                        'remediation': f"Update to one of: {', '.join(vuln.get('fix_versions', ['latest']))}"
                    })
        except Exception as e:
            results['pip_audit_error'] = str(e)
        
        # License compliance check
        try:
            pip_licenses_result = subprocess.run(
                ['pip-licenses', '--format=json'],
                capture_output=True, text=True, timeout=60
            )
            
            if pip_licenses_result.stdout:
                licenses_data = json.loads(pip_licenses_result.stdout)
                problematic_licenses = ['GPL', 'AGPL', 'SSPL', 'BUSL']
                
                for package in licenses_data:
                    license_name = package.get('License', 'Unknown')
                    if any(prob in license_name.upper() for prob in problematic_licenses):
                        results['license_compliance'].append({
                            'package': package.get('Name'),
                            'version': package.get('Version'),
                            'license': license_name,
                            'issue': 'Potentially problematic license for commercial use',
                            'action': 'Review license compatibility'
                        })
        except Exception as e:
            results['license_error'] = str(e)
        
        return results
    
    def _map_safety_severity(self, vuln_id: str) -> str:
        """Map Safety vulnerability ID to severity level"""
        high_risk_patterns = ['injection', 'rce', 'deserialization']
        if any(pattern in vuln_id.lower() for pattern in high_risk_patterns):
            return 'CRITICAL'
        return 'HIGH'  # Default for Safety findings
    
    def _calculate_severity_from_cvss(self, fix_versions: list) -> str:
        """Calculate severity based on fix version availability"""
        if not fix_versions:
            return 'HIGH'  # No fix available
        return 'MEDIUM'  # Fix available
```

### 2. OWASP Top 10 Assessment (Backend)

Check for backend-relevant OWASP Top 10 vulnerabilities:

**A01: Broken Access Control**
```python
# Check for missing authentication
def check_access_control():
    findings = []
    
    # API endpoints without auth
    unprotected_endpoints = [
        {'path': '/api/admin/*', 'method': 'GET', 'auth': False},
        {'path': '/api/users/delete', 'method': 'POST', 'auth': False}
    ]
    
    # Insecure direct object references
    idor_patterns = [
        r"user_id\s*=\s*request\.(GET|POST)\[",
        r"WHERE\s+id\s*=\s*\$_GET\[",
        r"findById\(req\.params\.id\)"
    ]
    
    # Missing authorization checks
    missing_authz = [
        {'file': '{{BE_PATH_API}}/admin.js', 'line': 45, 'issue': 'No role check'},
        {'file': 'api/delete.py', 'line': 12, 'issue': 'No ownership validation'}
    ]
    
    return findings
```

**A02: Cryptographic Failures**
```python
# Check encryption and hashing
crypto_issues = {
    "weak_hashing": [
        {"algorithm": "MD5", "usage": "password hashing", "severity": "CRITICAL"},
        {"algorithm": "SHA1", "usage": "token generation", "severity": "HIGH"}
    ],
    "insecure_storage": [
        {"data": "credit cards", "storage": "plain text in database"},
        {"data": "SSN", "storage": "base64 encoded only"}
    ],
    "missing_encryption": [
        {"connection": "database", "protocol": "unencrypted TCP"},
        {"api": "payment service", "protocol": "HTTP"}
    ],
    "weak_tls": [
        {"version": "TLS 1.0", "recommendation": "Use TLS 1.2+"},
        {"cipher": "DES-CBC3-SHA", "recommendation": "Use ECDHE-RSA-AES256-GCM-SHA384"}
    ]
}
```

**A03: Injection**
```python
# SQL Injection detection
sql_injection_tests = [
    {"payload": "' OR '1'='1", "vulnerable": True},
    {"payload": "'; DROP TABLE users; --", "vulnerable": True},
    {"payload": "1' UNION SELECT * FROM users--", "vulnerable": False}
]

# NoSQL Injection
nosql_injection = {
    "mongodb": [
        {"query": "db.users.find({username: req.body.username})", "vulnerable": True},
        {"fix": "db.users.find({username: {$eq: req.body.username}})"}
    ]
}

# Command Injection
command_injection = [
    {
        "code": "exec('ping ' + user_input)",
        "vulnerability": "Direct command execution with user input",
        "fix": "Use subprocess with shell=False and validate input"
    }
]
```

### 3. API Security

Comprehensive API security testing:

**Authentication & Authorization**
```python
# JWT Security Issues
jwt_vulnerabilities = {
    "weak_secret": {
        "issue": "JWT signed with weak secret 'secret123'",
        "severity": "CRITICAL",
        "fix": "Use strong 256-bit secret from environment"
    },
    "algorithm_confusion": {
        "issue": "JWT accepts 'none' algorithm",
        "severity": "CRITICAL",
        "fix": "Explicitly verify algorithm: ['HS256', 'RS256']"
    },
    "missing_expiration": {
        "issue": "JWT tokens never expire",
        "severity": "HIGH",
        "fix": "Set exp claim to reasonable duration (e.g., 1 hour)"
    }
}

# API Rate Limiting
rate_limit_config = {
    "endpoints": {
        "/api/login": {"limit": 5, "window": "5m", "status": "NOT_CONFIGURED"},
        "/api/password-reset": {"limit": 3, "window": "1h", "status": "NOT_CONFIGURED"},
        "/api/data": {"limit": 100, "window": "1m", "status": "OK"}
    }
}
```

**Input Validation**
```python
# API Input Validation Issues
validation_issues = [
    {
        "endpoint": "/api/users",
        "method": "POST",
        "field": "email",
        "issue": "No email format validation",
        "exploit": "user@<script>alert(1)</script>.com"
    },
    {
        "endpoint": "/api/upload",
        "method": "POST",
        "field": "file",
        "issue": "No file type validation",
        "exploit": "shell.php renamed to image.jpg"
    }
]
```

### 4. Secret Detection

Scan for exposed secrets and credentials:

**Secret Patterns**
```python
secret_patterns = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "aws_secret_key": r"[0-9a-zA-Z/+=]{40}",
    "github_token": r"ghp_[0-9a-zA-Z]{36}",
    "stripe_key": r"sk_live_[0-9a-zA-Z]{24}",
    "private_key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "google_api": r"AIza[0-9A-Za-z\-_]{35}",
    "jwt_token": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+",
    "slack_webhook": r"https://hooks\.slack\.com/services/[A-Z0-9]{9}/[A-Z0-9]{9}/[a-zA-Z0-9]{24}"
}

# Git history scan
def scan_git_history():
    """
    Scan git history for accidentally committed secrets
    """
    import subprocess
    
    # Get all commits
    commits = subprocess.run(
        ['git', 'log', '--pretty=format:%H'],
        capture_output=True,
        text=True
    ).stdout.split('\n')
    
    secrets_found = []
    
    for commit in commits[:100]:  # Last 100 commits
        diff = subprocess.run(
            ['git', 'show', commit],
            capture_output=True,
            text=True
        ).stdout
        
        for secret_type, pattern in secret_patterns.items():
            if re.search(pattern, diff):
                secrets_found.append({
                    'commit': commit,
                    'type': secret_type,
                    'action': 'Remove from history and rotate credential'
                })
    
    return secrets_found
```

### 5. Automated Remediation (Backend)

Provide intelligent, automated fixes for backend vulnerabilities:

**Smart Remediation Engine**
```python
import ast
import re
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RemediationAction:
    vulnerability_id: str
    action_type: str  # 'dependency_update', 'code_fix', 'config_change'
    description: str
    risk_level: str  # 'safe', 'low_risk', 'medium_risk', 'high_risk'
    automated: bool
    manual_steps: List[str]
    validation_tests: List[str]
    rollback_plan: str

class AutomatedRemediationEngine:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.backup_created = False
        self.applied_fixes = []
        
    def create_safety_backup(self) -> str:
        """Create git branch backup before applying fixes"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_branch = f'security_backup_{timestamp}'
        
        try:
            subprocess.run(['git', 'checkout', '-b', backup_branch], 
                         cwd=self.project_path, check=True)
            subprocess.run(['git', 'checkout', '-'], 
                         cwd=self.project_path, check=True)
            self.backup_created = True
            return backup_branch
        except subprocess.CalledProcessError:
            raise Exception("Failed to create safety backup branch")
    
    def apply_automated_fixes(self, vulnerabilities: List[Dict]) -> List[RemediationAction]:
        """Apply safe automated fixes"""
        if not self.backup_created:
            self.create_safety_backup()
        
        actions = []
        
        for vuln in vulnerabilities:
            action = self.generate_remediation_action(vuln)
            
            if action.automated and action.risk_level in ['safe', 'low_risk']:
                try:
                    success = self.apply_fix(action)
                    if success:
                        actions.append(action)
                        self.applied_fixes.append(action)
                except Exception as e:
                    print(f"Failed to apply fix for {action.vulnerability_id}: {e}")
            else:
                actions.append(action)
        
        return actions
    
    def generate_remediation_action(self, vulnerability: Dict) -> RemediationAction:
        """Generate specific remediation action for vulnerability"""
        vuln_type = vulnerability.get('type', '')
        severity = vulnerability.get('severity', 'MEDIUM')
        
        if vuln_type == 'vulnerable_dependency':
            return self._fix_vulnerable_dependency(vulnerability)
        elif vuln_type == 'sql_injection':
            return self._fix_sql_injection(vulnerability)
        elif vuln_type == 'hardcoded_secrets':
            return self._fix_hardcoded_secrets(vulnerability)
        else:
            return self._generic_fix(vulnerability)
    
    def _fix_vulnerable_dependency(self, vuln: Dict) -> RemediationAction:
        """Fix vulnerable dependencies automatically"""
        package = vuln.get('package', '')
        current_version = vuln.get('version', '')
        fixed_version = vuln.get('fixed_version', 'latest')
        
        # Determine package manager
        if (self.project_path / 'package.json').exists():
            update_command = f'npm install {package}@{fixed_version}'
            ecosystem = 'npm'
        elif (self.project_path / 'requirements.txt').exists():
            update_command = f'pip install {package}=={fixed_version}'
            ecosystem = 'pip'
        else:
            ecosystem = 'unknown'
            update_command = f'# Update {package} to {fixed_version}'
        
        return RemediationAction(
            vulnerability_id=vuln.get('id', ''),
            action_type='dependency_update',
            description=f'Update {package} from {current_version} to {fixed_version}',
            risk_level='safe',  # Dependency updates are generally safe
            automated=True,
            manual_steps=[
                f'Run: {update_command}',
                'Test application functionality',
                'Update lock file if needed'
            ],
            validation_tests=[
                f'Check {package} version is {fixed_version}',
                'Run regression tests',
                'Verify no new vulnerabilities introduced'
            ],
            rollback_plan=f'Revert to {package}@{current_version}'
        )
    
    def _fix_sql_injection(self, vuln: Dict) -> RemediationAction:
        """Fix SQL injection vulnerabilities"""
        file_path = vuln.get('file_path', '')
        line_number = vuln.get('line_number', 0)
        
        # Read the vulnerable code
        try:
            with open(self.project_path / file_path, 'r') as f:
                lines = f.readlines()
            
            vulnerable_line = lines[line_number - 1] if line_number > 0 else ''
            
            # Generate fix based on language and framework
            if file_path.endswith('.py'):
                fixed_code = self._fix_python_sql_injection(vulnerable_line)
            elif file_path.endswith('.js'):
                fixed_code = self._fix_javascript_sql_injection(vulnerable_line)
            else:
                fixed_code = '# Manual fix required'
            
            return RemediationAction(
                vulnerability_id=vuln.get('id', ''),
                action_type='code_fix',
                description=f'Fix SQL injection in {file_path}:{line_number}',
                risk_level='medium_risk',  # Code changes need testing
                automated=False,  # Require manual review
                manual_steps=[
                    f'Replace line {line_number} in {file_path}',
                    f'Original: {vulnerable_line.strip()}',
                    f'Fixed: {fixed_code}',
                    'Add input validation',
                    'Test with malicious inputs'
                ],
                validation_tests=[
                    'SQL injection penetration testing',
                    'Unit tests for the affected function',
                    'Integration tests for the endpoint'
                ],
                rollback_plan=f'Revert changes to {file_path}'
            )
        except Exception as e:
            return self._generic_fix(vuln)
    
    def _fix_python_sql_injection(self, vulnerable_line: str) -> str:
        """Generate Python SQL injection fix"""
        if 'cursor.execute(' in vulnerable_line and '{}' in vulnerable_line:
            return vulnerable_line.replace('.format(', ', (').replace('{}', '?')
        elif 'query(' in vulnerable_line and '+' in vulnerable_line:
            return '# Use parameterized query: query("SELECT * FROM table WHERE id = ?", (user_id,))'
        return '# Replace with parameterized query'
    
    def _fix_hardcoded_secrets(self, vuln: Dict) -> RemediationAction:
        """Fix hardcoded secrets"""
        file_path = vuln.get('file_path', '')
        secret_type = vuln.get('secret_type', 'credential')
        
        return RemediationAction(
            vulnerability_id=vuln.get('id', ''),
            action_type='code_fix',
            description=f'Remove hardcoded {secret_type} from {file_path}',
            risk_level='high_risk',  # Secrets need immediate attention
            automated=False,  # Never automate secret removal
            manual_steps=[
                f'Remove hardcoded secret from {file_path}',
                'Add secret to environment variables or secret manager',
                'Update code to read from environment',
                'Rotate the exposed credential',
                'Add {file_path} to .gitignore if needed',
                'Scan git history for credential exposure'
            ],
            validation_tests=[
                'Verify application works with environment variable',
                'Confirm no secrets in code',
                'Test with invalid/missing environment variable'
            ],
            rollback_plan='Use temporary hardcoded value until proper secret management'
        )
    
    def apply_fix(self, action: RemediationAction) -> bool:
        """Apply an automated fix"""
        if action.action_type == 'dependency_update':
            return self._apply_dependency_update(action)
        elif action.action_type == 'config_change':
            return self._apply_config_change(action)
        return False
    
    def _apply_dependency_update(self, action: RemediationAction) -> bool:
        """Apply dependency update"""
        try:
            # Extract update command from manual steps
            update_command = None
            for step in action.manual_steps:
                if step.startswith('Run: '):
                    update_command = step[5:].split()
                    break
            
            if update_command:
                result = subprocess.run(
                    update_command,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"Successfully applied: {action.description}")
                    return True
                else:
                    print(f"Failed to apply {action.description}: {result.stderr}")
                    return False
            
            return False
        except Exception as e:
            print(f"Error applying fix: {e}")
            return False
    
    def generate_remediation_report(self, actions: List[RemediationAction]) -> str:
        """Generate comprehensive remediation report"""
        report = []
        report.append("# Security Remediation Report\n")
        report.append(f"**Generated**: {datetime.now().isoformat()}\n")
        report.append(f"**Total Actions**: {len(actions)}\n")
        
        automated_count = sum(1 for a in actions if a.automated and a.risk_level in ['safe', 'low_risk'])
        manual_count = len(actions) - automated_count
        
        report.append(f"**Automated Fixes Applied**: {automated_count}\n")
        report.append(f"**Manual Actions Required**: {manual_count}\n\n")
        
        # Group by action type
        by_type = {}
        for action in actions:
            if action.action_type not in by_type:
                by_type[action.action_type] = []
            by_type[action.action_type].append(action)
        
        for action_type, type_actions in by_type.items():
            report.append(f"## {action_type.replace('_', ' ').title()}\n")
            
            for action in type_actions:
                report.append(f"### {action.description}\n")
                report.append(f"**Risk Level**: {action.risk_level}\n")
                report.append(f"**Automated**: {'Yes' if action.automated else 'No'}\n")
                
                if action.manual_steps:
                    report.append("**Manual Steps**:\n")
                    for step in action.manual_steps:
                        report.append(f"- {step}\n")
                
                if action.validation_tests:
                    report.append("**Validation Tests**:\n")
                    for test in action.validation_tests:
                        report.append(f"- {test}\n")
                
                report.append(f"**Rollback**: {action.rollback_plan}\n\n")
        
        return ''.join(report)
```

**Authentication Implementation**
```python
# Secure password handling
import bcrypt
from datetime import datetime, timedelta
import jwt
import secrets

class SecureAuth:
    def __init__(self):
        self.jwt_secret = os.environ.get('JWT_SECRET', secrets.token_urlsafe(32))
        self.password_min_length = 12
        
    def hash_password(self, password):
        """
        Securely hash password with bcrypt
        """
        # Validate password strength
        if len(password) < self.password_min_length:
            raise ValueError(f"Password must be at least {self.password_min_length} characters")
            
        # Check common passwords
        if password.lower() in self.load_common_passwords():
            raise ValueError("Password is too common")
            
        # Hash with bcrypt (cost factor 12)
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        """
        Verify password against hash
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id, expires_in=3600):
        """
        Generate secure JWT token
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # Unique token ID
        }
        
        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm='HS256'
        )
    
    def verify_token(self, token):
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
```

**Backend Security Middleware Templates**

*Express.js security middleware:*
```javascript
// Enhanced Express.js security middleware
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const mongoSanitize = require('express-mongo-sanitize');
const hpp = require('hpp');
const cors = require('cors');

// Advanced rate limiting
const createRateLimiter = (windowMs, max, message) => rateLimit({
    windowMs,
    max,
    message: { error: message },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
        res.status(429).json({
            error: message,
            retryAfter: Math.round(windowMs / 1000)
        });
    }
});

// Different limits for different endpoints
app.use('/api/auth/login', createRateLimiter(15 * 60 * 1000, 5, 'Too many login attempts'));
app.use('/api/auth/register', createRateLimiter(60 * 60 * 1000, 3, 'Too many registration attempts'));
app.use('/api/', createRateLimiter(15 * 60 * 1000, 100, 'Too many API requests'));

// CORS configuration
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true,
    optionsSuccessStatus: 200
}));

// Input sanitization and validation
app.use(express.json({ 
    limit: '10mb',
    verify: (req, res, buf) => {
        if (buf.length > 10 * 1024 * 1024) {
            throw new Error('Request entity too large');
        }
    }
}));
app.use(mongoSanitize()); // Prevent NoSQL injection
app.use(hpp()); // Prevent HTTP Parameter Pollution

// SQL injection prevention
const db = require('better-sqlite3')('app.db', {
    verbose: process.env.NODE_ENV === 'development' ? console.log : null
});

// Prepared statements
const statements = {
    getUserByEmail: db.prepare('SELECT * FROM users WHERE email = ?'),
    getUserById: db.prepare('SELECT * FROM users WHERE id = ?'),
    createUser: db.prepare('INSERT INTO users (email, password_hash) VALUES (?, ?)')
};

// Safe database operations
app.post('/login', async (req, res) => {
    const { email, password } = req.body;
    
    // Input validation
    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password required' });
    }
    
    try {
        const user = statements.getUserByEmail.get(email);
        if (user && await bcrypt.compare(password, user.password_hash)) {
            req.session.userId = user.id;
            res.json({ success: true, user: { id: user.id, email: user.email } });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
```

*Flask security configuration:*
```python
# Enhanced Flask security configuration
from flask import Flask, request, session, jsonify
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_seasurf import SeaSurf
from flask_cors import CORS
import bcrypt
import sqlite3
import os
import secrets

app = Flask(__name__)

# Security configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

# CORS configuration
CORS(app, {
    'origins': os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(','),
    'supports_credentials': True
})

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# CSRF protection
SeaSurf(app)

# Database connection with security
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
    return conn

# Secure password hashing
class PasswordManager:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Input validation
def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Secure login endpoint
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].strip().lower()
    password = data['password']
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    try:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, email, password_hash FROM users WHERE email = ?',
            (email,)
        ).fetchone()
        conn.close()
        
        if user and PasswordManager.verify_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session.permanent = True
            return jsonify({
                'success': True,
                'user': {'id': user['id'], 'email': user['email']}
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        app.logger.error(f'Login error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

# Request logging middleware
@app.before_request
def log_request_info():
    app.logger.info('Request: %s %s from %s', 
                   request.method, request.url, request.remote_addr)

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded', 'retry_after': e.retry_after}), 429

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0' if app.config.get('ENV') == 'production' else '127.0.0.1',
        port=int(os.environ.get('PORT', 5000)),
        debug=False  # Never enable debug in production
    )
```

<!-- Cross-reference: For frontend security headers (CSP, HSTS, etc.), see frontend/security-scan.md -->
<!-- Cross-reference: For CI/CD security integration and container scanning, see cloud/security-scan.md -->
<!-- Cross-reference: For security report generation and orchestration, see review/security-scan.md -->

## Output Format

1. **Tool Selection Matrix**: Recommended backend tools based on technology stack
2. **Comprehensive Scan Results**: Multi-tool aggregated findings
3. **Detailed Technical Findings**: Code-level vulnerabilities with fixes
4. **Automated Remediation Scripts**: Ready-to-run fix implementations
5. **Dependency Vulnerability Report**: Package-level security issues
6. **Secret Detection Results**: Exposed credentials and remediation steps

**Key Features**:
- Multi-tool integration: Bandit, Safety, Semgrep, Snyk, pip-audit
- Automated remediation: Smart dependency updates and code fixes
- Framework-specific: Tailored security patterns for Django, Flask, Express
- Actionable insights: Specific remediation code and deployment guidance

Focus on actionable remediation that can be implemented immediately while maintaining application functionality.
