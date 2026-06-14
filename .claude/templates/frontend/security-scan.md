---
model: claude-sonnet-4-0
description: Frontend Security Scanning
complexity: advanced
priority: critical
tags: ["security", "frontend", "auth"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Frontend Security Scanning

You are a security expert specializing in frontend application security, browser-side vulnerabilities, and client-side secure coding practices. Perform comprehensive frontend security audits to identify XSS, CSRF, clickjacking, and other client-side vulnerabilities with actionable remediation steps.

## Context
The user needs a thorough frontend security analysis covering DOM XSS scanning, CSP validation, security headers, and browser-side security patterns. Focus on OWASP Top 10 frontend-relevant categories including XSS, CSRF, and clickjacking with actionable remediation steps.

## Requirements
$ARGUMENTS

## Instructions

### 1. Security Scanning Tool Selection (Frontend)

Choose appropriate frontend security scanning tools:

**DOM XSS Scanners and CSP Validators**
```python
security_tools = {
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
    }
}
```

**SAST - Frontend-Specific Patterns**
```python
# Frontend-specific code vulnerability patterns
security_rules = {
    "xss": {
        "patterns": [
            r"innerHTML\s*=\s*[^\"']*\+",
            r"document\.write\s*\([^\"']*\+",
            r"dangerouslySetInnerHTML",
            r"v-html\s*=\s*[\"'][^\"']*\{"
        ],
        "severity": "HIGH",
        "cwe": "CWE-79",
        "fix": "Sanitize user input and use safe rendering methods"
    },
    
    "hardcoded_secrets": {
        "patterns": [
            r"(?i)(api[_-]?key|apikey|secret|password)\s*[:=]\s*[\"'][^\"']{8,}[\"']",
            r"(?i)bearer\s+[a-zA-Z0-9\-\._~\+\/]{20,}",
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
            r"require\s*\([^\"']*\+"
        ],
        "severity": "HIGH",
        "cwe": "CWE-22",
        "fix": "Validate and sanitize file paths"
    },
    
    "insecure_random": {
        "patterns": [
            r"Math\.random\(\)"
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-330",
        "fix": "Use cryptographically secure random functions (crypto.getRandomValues)"
    }
}

def scan_code_vulnerabilities(file_path, content):
    """
    Enhanced code vulnerability scanning for frontend code
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
                    'owasp_category': rule.get('owasp', 'A07:2021-XSS')
                })
    
    return vulnerabilities

# Framework-specific frontend security patterns
framework_security_patterns = {
    'react': {
        'dangerous_html': {
            'pattern': r'dangerouslySetInnerHTML',
            'severity': 'HIGH',
            'description': 'XSS vulnerability through innerHTML',
            'fix': 'Sanitize HTML content or use safe rendering'
        },
        'eval_usage': {
            'pattern': r'\beval\(',
            'severity': 'CRITICAL',
            'description': 'Code evaluation detected',
            'fix': 'Remove eval() usage'
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

### 2. OWASP Top 10 Assessment (Frontend)

Check for frontend-relevant OWASP Top 10 vulnerabilities:

**A03: Injection - XSS**
```python
# XSS vulnerability patterns
xss_patterns = {
    "dom_xss": {
        "sources": [
            r"document\.URL",
            r"document\.referrer",
            r"location\.hash",
            r"location\.search",
            r"window\.name"
        ],
        "sinks": [
            r"innerHTML\s*=",
            r"outerHTML\s*=",
            r"document\.write\(",
            r"document\.writeln\(",
            r"eval\(",
            r"setTimeout\([^,]*\+",
            r"setInterval\([^,]*\+"
        ],
        "severity": "HIGH",
        "cwe": "CWE-79",
        "fix": "Sanitize all user inputs before inserting into DOM; use textContent instead of innerHTML"
    },
    "reflected_xss": {
        "patterns": [
            r"dangerouslySetInnerHTML\s*=\s*\{\s*\{",
            r"v-html\s*=",
            r"\$\(.*\)\.html\(",
            r"\.append\([^)]*\+.*\)"
        ],
        "severity": "HIGH",
        "fix": "Use framework-provided safe rendering; escape HTML entities"
    },
    "stored_xss": {
        "patterns": [
            r"\.innerHTML\s*=\s*.*\bdata\b",
            r"\.innerHTML\s*=\s*.*\bresponse\b",
            r"\.innerHTML\s*=\s*.*\bresult\b"
        ],
        "severity": "CRITICAL",
        "fix": "Always sanitize server data before rendering; use DOMPurify or equivalent"
    }
}
```

**A05: Security Misconfiguration - CSRF**
```python
# CSRF vulnerability patterns
csrf_issues = {
    "missing_csrf_tokens": {
        "patterns": [
            r"<form\s+[^>]*method=[\"']POST[\"'][^>]*>(?!.*csrf)",
            r"fetch\([^)]*method:\s*[\"']POST[\"'][^)]*(?!.*csrf)"
        ],
        "severity": "HIGH",
        "description": "POST requests without CSRF token protection",
        "fix": "Include CSRF tokens in all state-changing requests"
    },
    "cors_misconfiguration": {
        "patterns": [
            r"Access-Control-Allow-Origin:\s*\*",
            r"origin:\s*[\"']\*[\"']"
        ],
        "severity": "HIGH",
        "description": "Wildcard CORS allows any origin",
        "fix": "Restrict allowed origins to trusted domains"
    },
    "same_site_cookie_missing": {
        "patterns": [
            r"document\.cookie\s*=\s*(?!.*SameSite)",
            r"Set-Cookie:(?!.*SameSite)"
        ],
        "severity": "MEDIUM",
        "description": "Cookies without SameSite attribute",
        "fix": "Set SameSite=Strict or SameSite=Lax on all cookies"
    }
}
```

**Clickjacking Protection**
```python
# Clickjacking vulnerability checks
clickjacking_issues = {
    "missing_x_frame_options": {
        "check": "Response header X-Frame-Options missing",
        "severity": "HIGH",
        "fix": "Set X-Frame-Options: DENY or SAMEORIGIN"
    },
    "missing_csp_frame_ancestors": {
        "check": "CSP frame-ancestors directive missing",
        "severity": "HIGH",
        "fix": "Add Content-Security-Policy: frame-ancestors 'self'"
    },
    "iframe_sandbox_missing": {
        "patterns": [
            r"<iframe\s+(?!.*sandbox)[^>]*>"
        ],
        "severity": "MEDIUM",
        "description": "iframes without sandbox attribute",
        "fix": "Add sandbox attribute to all iframes"
    }
}
```

### 3. Security Headers

Check HTTP security headers:

**Header Configuration**
```python
security_headers = {
    "Strict-Transport-Security": {
        "required": True,
        "value": "max-age=31536000; includeSubDomains; preload",
        "missing_impact": "Vulnerable to protocol downgrade attacks"
    },
    "X-Content-Type-Options": {
        "required": True,
        "value": "nosniff",
        "missing_impact": "Vulnerable to MIME type confusion attacks"
    },
    "X-Frame-Options": {
        "required": True,
        "value": "DENY",
        "missing_impact": "Vulnerable to clickjacking"
    },
    "Content-Security-Policy": {
        "required": True,
        "value": "default-src 'self'; script-src 'self' 'unsafe-inline'",
        "missing_impact": "Vulnerable to XSS attacks"
    },
    "X-XSS-Protection": {
        "required": False,  # Deprecated
        "value": "0",
        "note": "Modern browsers have built-in XSS protection"
    },
    "Referrer-Policy": {
        "required": True,
        "value": "strict-origin-when-cross-origin",
        "missing_impact": "May leak sensitive URLs"
    },
    "Permissions-Policy": {
        "required": True,
        "value": "geolocation=(), microphone=(), camera=()",
        "missing_impact": "Allows access to sensitive browser features"
    }
}
```

### 4. Automated Remediation (Frontend)

Provide intelligent, automated fixes for frontend security issues:

**Frontend Security Middleware - Express.js with Helmet**
```javascript
// Enhanced Express.js security middleware for frontend serving
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

// Content Security Policy
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'", "https://trusted-cdn.com"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'"],
            fontSrc: ["'self'", "https://fonts.gstatic.com"],
            objectSrc: ["'none'"],
            mediaSrc: ["'self'"],
            frameSrc: ["'none'"],
            baseUri: ["'self'"],
            formAction: ["'self'"]
        },
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    },
    noSniff: true,
    xssFilter: true,
    referrerPolicy: { policy: 'same-origin' }
}));

// CORS configuration
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true,
    optionsSuccessStatus: 200
}));

// Custom security middleware
app.use((req, res, next) => {
    // Remove sensitive headers
    res.removeHeader('X-Powered-By');
    
    // Add security headers
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    
    next();
});

// Secure session configuration
app.use(session({
    secret: process.env.SESSION_SECRET || throwError('SESSION_SECRET required'),
    name: 'sessionId', // Don't use default 'connect.sid'
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000, // 24 hours
        sameSite: 'strict'
    },
    store: new RedisStore({ /* Redis configuration */ })
}));
```

**Frontend Security Middleware - Flask with Talisman**
```python
# Flask security configuration for frontend-facing routes
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)

# HTTPS enforcement and security headers
Talisman(app, {
    'force_https': app.config.get('ENV') == 'production',
    'strict_transport_security': True,
    'strict_transport_security_max_age': 31536000,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
        'font-src': "'self' https://fonts.gstatic.com",
        'img-src': "'self' data: https:",
        'connect-src': "'self'",
        'frame-src': "'none'",
        'object-src': "'none'"
    },
    'referrer_policy': 'strict-origin-when-cross-origin'
})
```

**Client-Side Security Patterns**
```javascript
// DOMPurify for safe HTML rendering
import DOMPurify from 'dompurify';

// Safe innerHTML alternative
function safeSetHTML(element, untrustedHTML) {
    element.innerHTML = DOMPurify.sanitize(untrustedHTML, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
        ALLOWED_ATTR: ['href', 'target'],
        ALLOW_DATA_ATTR: false
    });
}

// CSP violation reporting
document.addEventListener('securitypolicyviolation', (event) => {
    fetch('/api/csp-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            blockedUri: event.blockedURI,
            violatedDirective: event.violatedDirective,
            originalPolicy: event.originalPolicy,
            sourceFile: event.sourceFile,
            lineNumber: event.lineNumber
        })
    });
});

// Secure cookie handling
function setSecureCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; Secure; HttpOnly; SameSite=Strict`;
}

// Input sanitization utilities
const sanitize = {
    html: (input) => DOMPurify.sanitize(input),
    url: (input) => {
        try {
            const url = new URL(input);
            if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Invalid protocol');
            return url.toString();
        } catch {
            return '';
        }
    },
    text: (input) => input.replace(/[<>&"']/g, (c) => ({
        '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
    })[c])
};
```

<!-- Cross-reference: For backend API security (JWT, rate limiting, SQL injection), see backend/security-scan.md -->
<!-- Cross-reference: For CI/CD security integration and container scanning, see cloud/security-scan.md -->
<!-- Cross-reference: For security report generation and orchestration, see review/security-scan.md -->

## Output Format

1. **Tool Selection Matrix**: Recommended frontend tools based on technology stack
2. **XSS Vulnerability Report**: DOM, reflected, and stored XSS findings
3. **Security Headers Audit**: Missing or misconfigured HTTP security headers
4. **CSRF/Clickjacking Assessment**: Client-side protection gaps
5. **CSP Configuration Report**: Content Security Policy analysis and recommendations
6. **Automated Remediation Scripts**: Ready-to-use frontend security fixes

**Key Features**:
- DOM XSS detection: Source-to-sink analysis for JavaScript
- CSP validation: Content Security Policy completeness checking
- Framework-specific: Tailored patterns for React, Vue, Angular
- Security headers: Complete HTTP security header validation
- Client-side protection: CSRF, clickjacking, and cookie security

Focus on actionable remediation that can be implemented immediately while maintaining application functionality.
