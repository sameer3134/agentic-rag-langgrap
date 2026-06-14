---
model: claude-sonnet-4-0
description: "Backend Error Tracking, Logging & Recovery"
complexity: advanced
priority: high
tags: [error-handling, logging, backend, monitoring]
depends_on: []
chains_to: [cloud/error-trace]
skip_if: []
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Backend Error Tracking, Logging & Recovery

You are an error tracking and observability expert specializing in implementing comprehensive backend error monitoring solutions. Set up error tracking systems, implement structured logging, error grouping, and ensure teams can quickly identify and resolve production issues.

## Context
The user needs to implement or improve backend error tracking, structured logging, error grouping, and recovery strategies. Focus on service integration, structured logging, intelligent error grouping, and automatic recovery.

## Requirements
$ARGUMENTS

## Instructions

### 1. Error Tracking Analysis

Analyze current error handling and tracking:

**Error Analysis Script**
```python
import os
import re
import ast
from pathlib import Path
from collections import defaultdict

class ErrorTrackingAnalyzer:
    def analyze_codebase(self, project_path):
        """
        Analyze error handling patterns in codebase
        """
        analysis = {
            'error_handling': self._analyze_error_handling(project_path),
            'logging_usage': self._analyze_logging(project_path),
            'monitoring_setup': self._check_monitoring_setup(project_path),
            'error_patterns': self._identify_error_patterns(project_path),
            'recommendations': []
        }
        
        self._generate_recommendations(analysis)
        return analysis
    
    def _analyze_error_handling(self, project_path):
        """Analyze error handling patterns"""
        patterns = {
            'try_catch_blocks': 0,
            'unhandled_promises': 0,
            'generic_catches': 0,
            'error_types': defaultdict(int),
            'error_reporting': []
        }
        
        for file_path in Path(project_path).rglob('*.{js,ts,py,java,go}'):
            content = file_path.read_text(errors='ignore')
            
            # JavaScript/{{LANGUAGE}} patterns
            if file_path.suffix in ['.js', '.ts']:
                patterns['try_catch_blocks'] += len(re.findall(r'try\s*{', content))
                patterns['generic_catches'] += len(re.findall(r'catch\s*\([^)]*\)\s*{\s*}', content))
                patterns['unhandled_promises'] += len(re.findall(r'\.then\([^)]+\)(?!\.catch)', content))
            
            # {{LANGUAGE}} patterns
            elif file_path.suffix == '.py':
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Try):
                            patterns['try_catch_blocks'] += 1
                            for handler in node.handlers:
                                if handler.type is None:
                                    patterns['generic_catches'] += 1
                except:
                    pass
        
        return patterns
    
    def _analyze_logging(self, project_path):
        """Analyze logging patterns"""
        logging_patterns = {
            'console_logs': 0,
            'structured_logging': False,
            'log_levels_used': set(),
            'logging_frameworks': []
        }
        
        # Check for logging frameworks
        package_files = ['package.json', 'requirements.txt', 'go.mod', 'pom.xml']
        for pkg_file in package_files:
            pkg_path = Path(project_path) / pkg_file
            if pkg_path.exists():
                content = pkg_path.read_text()
                if 'winston' in content or 'bunyan' in content:
                    logging_patterns['logging_frameworks'].append('winston/bunyan')
                if 'pino' in content:
                    logging_patterns['logging_frameworks'].append('pino')
                if 'logging' in content:
                    logging_patterns['logging_frameworks'].append('python-logging')
                if 'logrus' in content or 'zap' in content:
                    logging_patterns['logging_frameworks'].append('logrus/zap')
        
        return logging_patterns
```

### 2. Error Tracking Service Integration

Implement integrations with popular error tracking services:

**{{CLOUD_ERROR_TRACKER}} Integration**
```javascript
// sentry-setup.js
import * as {{CLOUD_ERROR_TRACKER}} from "@sentry/node";
import { ProfilingIntegration } from "@sentry/profiling-node";

class SentryErrorTracker {
    constructor(config) {
        this.config = config;
        this.initialized = false;
    }
    
    initialize() {
        {{CLOUD_ERROR_TRACKER}}.init({
            dsn: this.config.dsn,
            environment: this.config.environment,
            release: this.config.release,
            
            // Performance Monitoring
            tracesSampleRate: this.config.tracesSampleRate || 0.1,
            profilesSampleRate: this.config.profilesSampleRate || 0.1,
            
            // Integrations
            integrations: [
                // HTTP integration
                new {{CLOUD_ERROR_TRACKER}}.Integrations.Http({ tracing: true }),
                
                // {{BE_FRAMEWORK}} integration
                new {{CLOUD_ERROR_TRACKER}}.Integrations.{{BE_FRAMEWORK}}({
                    app: this.config.app,
                    router: true,
                    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
                }),
                
                // Database integration
                new {{CLOUD_ERROR_TRACKER}}.Integrations.Postgres(),
                new {{CLOUD_ERROR_TRACKER}}.Integrations.Mysql(),
                new {{CLOUD_ERROR_TRACKER}}.Integrations.Mongo(),
                
                // Profiling
                new ProfilingIntegration(),
                
                // Custom integrations
                ...this.getCustomIntegrations()
            ],
            
            // Filtering
            beforeSend: (event, hint) => {
                // Filter sensitive data
                if (event.request?.cookies) {
                    delete event.request.cookies;
                }
                
                // Filter out specific errors
                if (this.shouldFilterError(event, hint)) {
                    return null;
                }
                
                // Enhance error context
                return this.enhanceErrorEvent(event, hint);
            },
            
            // Breadcrumbs
            beforeBreadcrumb: (breadcrumb, hint) => {
                // Filter sensitive breadcrumbs
                if (breadcrumb.category === 'console' && breadcrumb.level === 'debug') {
                    return null;
                }
                
                return breadcrumb;
            },
            
            // Options
            attachStacktrace: true,
            shutdownTimeout: 5000,
            maxBreadcrumbs: 100,
            debug: this.config.debug || false,
            
            // Tags
            initialScope: {
                tags: {
                    component: this.config.component,
                    version: this.config.version
                },
                user: {
                    id: this.config.userId,
                    segment: this.config.userSegment
                }
            }
        });
        
        this.initialized = true;
        this.setupErrorHandlers();
    }
    
    setupErrorHandlers() {
        // Global error handler
        process.on('uncaughtException', (error) => {
            console.error('Uncaught Exception:', error);
            {{CLOUD_ERROR_TRACKER}}.captureException(error, {
                tags: { type: 'uncaught_exception' },
                level: 'fatal'
            });
            
            // Graceful shutdown
            this.gracefulShutdown();
        });
        
        // Promise rejection handler
        process.on('unhandledRejection', (reason, promise) => {
            console.error('Unhandled Rejection:', reason);
            {{CLOUD_ERROR_TRACKER}}.captureException(reason, {
                tags: { type: 'unhandled_rejection' },
                extra: { promise: promise.toString() }
            });
        });
    }
    
    enhanceErrorEvent(event, hint) {
        // Add custom context
        event.extra = {
            ...event.extra,
            memory: process.memoryUsage(),
            uptime: process.uptime(),
            nodeVersion: process.version
        };
        
        // Add user context
        if (this.config.getUserContext) {
            event.user = this.config.getUserContext();
        }
        
        // Add custom fingerprinting
        if (hint.originalException) {
            event.fingerprint = this.generateFingerprint(hint.originalException);
        }
        
        return event;
    }
    
    generateFingerprint(error) {
        // Custom fingerprinting logic
        const fingerprint = [];
        
        // Group by error type
        fingerprint.push(error.name || 'Error');
        
        // Group by error location
        if (error.stack) {
            const match = error.stack.match(/at\s+(.+?)\s+\(/);
            if (match) {
                fingerprint.push(match[1]);
            }
        }
        
        // Group by custom properties
        if (error.code) {
            fingerprint.push(error.code);
        }
        
        return fingerprint;
    }
}

// {{BE_FRAMEWORK}} middleware
export const sentryMiddleware = {
    requestHandler: {{CLOUD_ERROR_TRACKER}}.Handlers.requestHandler(),
    tracingHandler: {{CLOUD_ERROR_TRACKER}}.Handlers.tracingHandler(),
    errorHandler: {{CLOUD_ERROR_TRACKER}}.Handlers.errorHandler({
        shouldHandleError(error) {
            // Capture 4xx and 5xx errors
            if (error.status >= 400) {
                return true;
            }
            return false;
        }
    })
};
```

**Custom Error Tracking Service**
```typescript
// error-tracker.ts
interface ErrorEvent {
    timestamp: Date;
    level: 'debug' | 'info' | 'warning' | 'error' | 'fatal';
    message: string;
    stack?: string;
    context: {
        user?: any;
        request?: any;
        environment: string;
        release: string;
        tags: Record<string, string>;
        extra: Record<string, any>;
    };
    fingerprint: string[];
}

class ErrorTracker {
    private queue: ErrorEvent[] = [];
    private batchSize = 10;
    private flushInterval = 5000;
    
    constructor(private config: ErrorTrackerConfig) {
        this.startBatchProcessor();
    }
    
    captureException(error: Error, context?: Partial<ErrorEvent['context']>) {
        const event: ErrorEvent = {
            timestamp: new Date(),
            level: 'error',
            message: error.message,
            stack: error.stack,
            context: {
                environment: this.config.environment,
                release: this.config.release,
                tags: {},
                extra: {},
                ...context
            },
            fingerprint: this.generateFingerprint(error)
        };
        
        this.addToQueue(event);
    }
    
    captureMessage(message: string, level: ErrorEvent['level'] = 'info') {
        const event: ErrorEvent = {
            timestamp: new Date(),
            level,
            message,
            context: {
                environment: this.config.environment,
                release: this.config.release,
                tags: {},
                extra: {}
            },
            fingerprint: [message]
        };
        
        this.addToQueue(event);
    }
    
    private addToQueue(event: ErrorEvent) {
        // Apply sampling
        if (Math.random() > this.config.sampleRate) {
            return;
        }
        
        // Filter sensitive data
        event = this.sanitizeEvent(event);
        
        // Add to queue
        this.queue.push(event);
        
        // Flush if queue is full
        if (this.queue.length >= this.batchSize) {
            this.flush();
        }
    }
    
    private sanitizeEvent(event: ErrorEvent): ErrorEvent {
        // Remove sensitive data
        const sensitiveKeys = ['password', 'token', 'secret', 'api_key'];
        
        const sanitize = (obj: any): any => {
            if (!obj || typeof obj !== 'object') return obj;
            
            const cleaned = Array.isArray(obj) ? [] : {};
            
            for (const [key, value] of Object.entries(obj)) {
                if (sensitiveKeys.some(k => key.toLowerCase().includes(k))) {
                    cleaned[key] = '[REDACTED]';
                } else if (typeof value === 'object') {
                    cleaned[key] = sanitize(value);
                } else {
                    cleaned[key] = value;
                }
            }
            
            return cleaned;
        };
        
        return {
            ...event,
            context: sanitize(event.context)
        };
    }
    
    private async flush() {
        if (this.queue.length === 0) return;
        
        const events = this.queue.splice(0, this.batchSize);
        
        try {
            await this.sendEvents(events);
        } catch (error) {
            console.error('Failed to send error events:', error);
            // Re-queue events
            this.queue.unshift(...events);
        }
    }
    
    private async sendEvents(events: ErrorEvent[]) {
        const response = await fetch(this.config.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.config.apiKey}`
            },
            body: JSON.stringify({ events })
        });
        
        if (!response.ok) {
            throw new Error(`Error tracking API returned ${response.status}`);
        }
    }
}
```

### 3. Structured Logging Implementation

Implement comprehensive structured logging:

**Advanced Logger**
```typescript
// structured-logger.ts
import winston from 'winston';
import { ElasticsearchTransport } from 'winston-elasticsearch';

class StructuredLogger {
    private logger: winston.Logger;
    
    constructor(config: LoggerConfig) {
        this.logger = winston.createLogger({
            level: config.level || 'info',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.errors({ stack: true }),
                winston.format.metadata(),
                winston.format.json()
            ),
            defaultMeta: {
                service: config.service,
                environment: config.environment,
                version: config.version
            },
            transports: this.createTransports(config)
        });
    }
    
    private createTransports(config: LoggerConfig): winston.transport[] {
        const transports: winston.transport[] = [];
        
        // Console transport for development
        if (config.environment === 'development') {
            transports.push(new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    winston.format.simple()
                )
            }));
        }
        
        // File transport for all environments
        transports.push(new winston.transports.File({
            filename: '{{CLOUD_PATH_LOGS}}/error.log',
            level: 'error',
            maxsize: 5242880, // 5MB
            maxFiles: 5
        }));
        
        transports.push(new winston.transports.File({
            filename: '{{CLOUD_PATH_LOGS}}/combined.log',
            maxsize: 5242880,
            maxFiles: 5
        });
        
        // {{CLOUD_LOG_STACK}} transport for production
        if (config.elasticsearch) {
            transports.push(new ElasticsearchTransport({
                level: 'info',
                clientOpts: config.elasticsearch,
                index: `logs-${config.service}`,
                transformer: (logData) => {
                    return {
                        '@timestamp': logData.timestamp,
                        severity: logData.level,
                        message: logData.message,
                        fields: {
                            ...logData.metadata,
                            ...logData.defaultMeta
                        }
                    };
                }
            }));
        }
        
        return transports;
    }
    
    // Logging methods with context
    error(message: string, error?: Error, context?: any) {
        this.logger.error(message, {
            error: {
                message: error?.message,
                stack: error?.stack,
                name: error?.name
            },
            ...context
        });
    }
    
    warn(message: string, context?: any) {
        this.logger.warn(message, context);
    }
    
    info(message: string, context?: any) {
        this.logger.info(message, context);
    }
    
    debug(message: string, context?: any) {
        this.logger.debug(message, context);
    }
    
    // Performance logging
    startTimer(label: string): () => void {
        const start = Date.now();
        return () => {
            const duration = Date.now() - start;
            this.info(`Timer ${label}`, { duration, label });
        };
    }
    
    // Audit logging
    audit(action: string, userId: string, details: any) {
        this.info('Audit Event', {
            type: 'audit',
            action,
            userId,
            timestamp: new Date().toISOString(),
            details
        });
    }
}

// Request logging middleware
export function requestLoggingMiddleware(logger: StructuredLogger) {
    return (req: Request, res: Response, next: NextFunction) => {
        const start = Date.now();
        
        // Log request
        logger.info('Incoming request', {
            method: req.method,
            url: req.url,
            ip: req.ip,
            userAgent: req.get('user-agent')
        });
        
        // Log response
        res.on('finish', () => {
            const duration = Date.now() - start;
            logger.info('Request completed', {
                method: req.method,
                url: req.url,
                status: res.statusCode,
                duration,
                contentLength: res.get('content-length')
            });
        });
        
        next();
    };
}
```

### 4. Error Grouping and Deduplication

Implement intelligent error grouping:

**Error Grouping Algorithm**
```python
import hashlib
import re
from difflib import SequenceMatcher

class ErrorGrouper:
    def __init__(self):
        self.groups = {}
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for normalization"""
        return {
            'numbers': re.compile(r'\b\d+\b'),
            'uuids': re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'),
            'urls': re.compile(r'https?://[^\s]+'),
            'file_paths': re.compile(r'(/[^/\s]+)+'),
            'memory_addresses': re.compile(r'0x[0-9a-fA-F]+'),
            'timestamps': re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}')
        }
    
    def group_error(self, error):
        """Group error with similar errors"""
        fingerprint = self.generate_fingerprint(error)
        
        # Find existing group
        group = self.find_similar_group(fingerprint, error)
        
        if group:
            group['count'] += 1
            group['last_seen'] = error['timestamp']
            group['instances'].append(error)
        else:
            # Create new group
            self.groups[fingerprint] = {
                'fingerprint': fingerprint,
                'first_seen': error['timestamp'],
                'last_seen': error['timestamp'],
                'count': 1,
                'instances': [error],
                'pattern': self.extract_pattern(error)
            }
        
        return fingerprint
    
    def generate_fingerprint(self, error):
        """Generate unique fingerprint for error"""
        # Normalize error message
        normalized = self.normalize_message(error['message'])
        
        # Include error type and location
        components = [
            error.get('type', 'Unknown'),
            normalized,
            self.extract_location(error.get('stack', ''))
        ]
        
        # Generate hash
        fingerprint = hashlib.sha256(
            '|'.join(components).encode()
        ).hexdigest()[:16]
        
        return fingerprint
    
    def normalize_message(self, message):
        """Normalize error message for grouping"""
        # Replace dynamic values
        normalized = message
        for pattern_name, pattern in self.patterns.items():
            normalized = pattern.sub(f'<{pattern_name}>', normalized)
        
        return normalized.strip()
    
    def extract_location(self, stack):
        """Extract error location from stack trace"""
        if not stack:
            return 'unknown'
        
        lines = stack.split('\n')
        for line in lines:
            # Look for file references
            if ' at ' in line:
                # Extract file and line number
                match = re.search(r'at\s+(.+?)\s*\((.+?):(\d+):(\d+)\)', line)
                if match:
                    file_path = match.group(2)
                    # Normalize file path
                    file_path = re.sub(r'.*/(?=src/|lib/|app/)', '', file_path)
                    return f"{file_path}:{match.group(3)}"
        
        return 'unknown'
    
    def find_similar_group(self, fingerprint, error):
        """Find similar error group using fuzzy matching"""
        if fingerprint in self.groups:
            return self.groups[fingerprint]
        
        # Try fuzzy matching
        normalized_message = self.normalize_message(error['message'])
        
        for group_fp, group in self.groups.items():
            similarity = SequenceMatcher(
                None,
                normalized_message,
                group['pattern']
            ).ratio()
            
            if similarity > 0.85:  # 85% similarity threshold
                return group
        
        return None
```

### 5. Error Recovery Strategies

Implement automatic error recovery:

**Recovery Manager**
```javascript
// recovery-manager.js
class RecoveryManager {
    constructor(config) {
        this.strategies = new Map();
        this.retryPolicies = config.retryPolicies || {};
        this.circuitBreakers = new Map();
        this.registerDefaultStrategies();
    }
    
    registerStrategy(errorType, strategy) {
        this.strategies.set(errorType, strategy);
    }
    
    registerDefaultStrategies() {
        // Network errors
        this.registerStrategy('NetworkError', async (error, context) => {
            return this.retryWithBackoff(
                context.operation,
                this.retryPolicies.network || {
                    maxRetries: 3,
                    baseDelay: 1000,
                    maxDelay: 10000
                }
            );
        });
        
        // Database errors
        this.registerStrategy('DatabaseError', async (error, context) => {
            // Try read replica if available
            if (context.operation.type === 'read' && context.readReplicas) {
                return this.tryReadReplica(context);
            }
            
            // Otherwise retry with backoff
            return this.retryWithBackoff(
                context.operation,
                this.retryPolicies.database || {
                    maxRetries: 2,
                    baseDelay: 500,
                    maxDelay: 5000
                }
            );
        });
        
        // Rate limit errors
        this.registerStrategy('RateLimitError', async (error, context) => {
            const retryAfter = error.retryAfter || 60;
            await this.delay(retryAfter * 1000);
            return context.operation();
        });
        
        // Circuit breaker for external services
        this.registerStrategy('ExternalServiceError', async (error, context) => {
            const breaker = this.getCircuitBreaker(context.service);
            
            try {
                return await breaker.execute(context.operation);
            } catch (error) {
                // Fallback to cache or default
                if (context.fallback) {
                    return context.fallback();
                }
                throw error;
            }
        });
    }
    
    async recover(error, context) {
        const errorType = this.classifyError(error);
        const strategy = this.strategies.get(errorType);
        
        if (!strategy) {
            // No recovery strategy, rethrow
            throw error;
        }
        
        try {
            const result = await strategy(error, context);
            
            // Log recovery success
            this.logRecovery(error, errorType, 'success');
            
            return result;
        } catch (recoveryError) {
            // Log recovery failure
            this.logRecovery(error, errorType, 'failure', recoveryError);
            
            // Throw original error
            throw error;
        }
    }
    
    async retryWithBackoff(operation, policy) {
        let lastError;
        let delay = policy.baseDelay;
        
        for (let attempt = 0; attempt < policy.maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;
                
                if (attempt < policy.maxRetries - 1) {
                    await this.delay(delay);
                    delay = Math.min(delay * 2, policy.maxDelay);
                }
            }
        }
        
        throw lastError;
    }
    
    getCircuitBreaker(service) {
        if (!this.circuitBreakers.has(service)) {
            this.circuitBreakers.set(service, new CircuitBreaker({
                timeout: 3000,
                errorThresholdPercentage: 50,
                resetTimeout: 30000,
                rollingCountTimeout: 10000,
                rollingCountBuckets: 10,
                volumeThreshold: 10
            }));
        }
        
        return this.circuitBreakers.get(service);
    }
    
    classifyError(error) {
        // Classify by error code
        if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
            return 'NetworkError';
        }
        
        if (error.code === 'ER_LOCK_DEADLOCK' || error.code === 'SQLITE_BUSY') {
            return 'DatabaseError';
        }
        
        if (error.status === 429) {
            return 'RateLimitError';
        }
        
        if (error.isExternalService) {
            return 'ExternalServiceError';
        }
        
        // Default
        return 'UnknownError';
    }
}

// Circuit breaker implementation
class CircuitBreaker {
    constructor(options) {
        this.options = options;
        this.state = 'CLOSED';
        this.failures = 0;
        this.successes = 0;
        this.nextAttempt = Date.now();
    }
    
    async execute(operation) {
        if (this.state === 'OPEN') {
            if (Date.now() < this.nextAttempt) {
                throw new Error('Circuit breaker is OPEN');
            }
            
            // Try half-open
            this.state = 'HALF_OPEN';
        }
        
        try {
            const result = await Promise.race([
                operation(),
                this.timeout(this.options.timeout)
            ]);
            
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }
    
    onSuccess() {
        this.failures = 0;
        
        if (this.state === 'HALF_OPEN') {
            this.successes++;
            if (this.successes >= this.options.volumeThreshold) {
                this.state = 'CLOSED';
                this.successes = 0;
            }
        }
    }
    
    onFailure() {
        this.failures++;
        
        if (this.state === 'HALF_OPEN') {
            this.state = 'OPEN';
            this.nextAttempt = Date.now() + this.options.resetTimeout;
        } else if (this.failures >= this.options.volumeThreshold) {
            this.state = 'OPEN';
            this.nextAttempt = Date.now() + this.options.resetTimeout;
        }
    }
}
```

## Output Format

1. **Error Tracking Analysis**: Current error handling assessment
2. **Integration Configuration**: Setup for error tracking services
3. **Logging Implementation**: Structured logging setup
4. **Error Grouping**: Deduplication and grouping logic
5. **Recovery Strategies**: Automatic error recovery implementation
6. **Documentation**: Implementation and troubleshooting guide

Focus on providing comprehensive backend error handling, structured logging, intelligent grouping, and robust recovery strategies.

<!-- Cross-reference: For error alerting, performance monitoring, and dashboards, see cloud/error-trace.md -->
