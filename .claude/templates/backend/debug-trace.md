---
description: "Backend Debugging & Logging"
model: claude-sonnet-4-0
complexity: intermediate
priority: high
tags: [debug, logging, backend, tracing]
depends_on: []
chains_to: []
skip_if: []
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Backend Debugging & Logging

You are a debugging expert specializing in setting up comprehensive backend debugging environments and structured logging. Configure IDE debugger workflows, implement logging frameworks, and establish troubleshooting practices for backend development.

## Context
The user needs to set up backend debugging and logging capabilities to efficiently diagnose issues, track down bugs, and understand system behavior. Focus on developer productivity, IDE integration for debugging, and comprehensive structured logging strategies.

## Requirements
$ARGUMENTS

## Instructions

### 1. Development Environment Debugging

Set up comprehensive debugging environments:

**VS Code Debug Configuration**
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug {{LANGUAGE}} App",
            "type": "node",
            "request": "launch",
            "runtimeExecutable": "node",
            "runtimeArgs": ["--inspect-brk", "--enable-source-maps"],
            "program": "${workspaceFolder}/src/index.js",
            "env": {
                "NODE_ENV": "development",
                "DEBUG": "*",
                "NODE_OPTIONS": "--max-old-space-size=4096"
            },
            "sourceMaps": true,
            "resolveSourceMapLocations": [
                "${workspaceFolder}/**",
                "!**/node_modules/**"
            ],
            "skipFiles": [
                "<node_internals>/**",
                "node_modules/**"
            ],
            "console": "integratedTerminal",
            "outputCapture": "std"
        },
        {
            "name": "Debug {{LANGUAGE}}",
            "type": "node",
            "request": "launch",
            "program": "${workspaceFolder}/src/index.ts",
            "preLaunchTask": "tsc: build - tsconfig.json",
            "outFiles": ["${workspaceFolder}/dist/**/*.js"],
            "sourceMaps": true,
            "smartStep": true,
            "internalConsoleOptions": "openOnSessionStart"
        },
        {
            "name": "Debug Jest Tests",
            "type": "node",
            "request": "launch",
            "program": "${workspaceFolder}/node_modules/.bin/jest",
            "args": [
                "--runInBand",
                "--no-cache",
                "--watchAll=false",
                "--detectOpenHandles"
            ],
            "console": "integratedTerminal",
            "internalConsoleOptions": "neverOpen",
            "env": {
                "NODE_ENV": "test"
            }
        },
        {
            "name": "Attach to Process",
            "type": "node",
            "request": "attach",
            "processId": "${command:PickProcess}",
            "protocol": "inspector",
            "restart": true,
            "sourceMaps": true
        }
    ],
    "compounds": [
        {
            "name": "Full Stack Debug",
            "configurations": ["Debug Backend", "Debug Frontend"],
            "stopAll": true
        }
    ]
}
```

**Chrome DevTools Configuration**
```javascript
// debug-helpers.js
class DebugHelper {
    constructor() {
        this.setupDevTools();
        this.setupConsoleHelpers();
        this.setupPerformanceMarkers();
    }
    
    setupDevTools() {
        if (typeof window !== 'undefined') {
            // Add debug namespace
            window.DEBUG = window.DEBUG || {};
            
            // Store references to important objects
            window.DEBUG.store = () => window.__REDUX_STORE__;
            window.DEBUG.router = () => window.__ROUTER__;
            window.DEBUG.components = new Map();
            
            // Performance debugging
            window.DEBUG.measureRender = (componentName) => {
                performance.mark(`${componentName}-start`);
                return () => {
                    performance.mark(`${componentName}-end`);
                    performance.measure(
                        componentName,
                        `${componentName}-start`,
                        `${componentName}-end`
                    );
                };
            };
            
            // Memory debugging
            window.DEBUG.heapSnapshot = async () => {
                if ('memory' in performance) {
                    const snapshot = await performance.measureUserAgentSpecificMemory();
                    console.table(snapshot);
                    return snapshot;
                }
            };
        }
    }
    
    setupConsoleHelpers() {
        // Enhanced console logging
        const styles = {
            error: 'color: #ff0000; font-weight: bold;',
            warn: 'color: #ff9800; font-weight: bold;',
            info: 'color: #2196f3; font-weight: bold;',
            debug: 'color: #4caf50; font-weight: bold;',
            trace: 'color: #9c27b0; font-weight: bold;'
        };
        
        Object.entries(styles).forEach(([level, style]) => {
            const original = console[level];
            console[level] = function(...args) {
                if (process.env.NODE_ENV === 'development') {
                    const timestamp = new Date().toISOString();
                    original.call(console, `%c[${timestamp}] ${level.toUpperCase()}:`, style, ...args);
                }
            };
        });
    }
}

// {{FE_FRAMEWORK}} DevTools integration
if (process.env.NODE_ENV === 'development') {
    // Expose {{FE_FRAMEWORK}} internals
    window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = {
        ...window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        onCommitFiberRoot: (id, root) => {
            // Custom commit logging
            console.debug('{{FE_FRAMEWORK}} commit:', root);
        }
    };
}
```

### 4. Debug Logging Framework

Implement structured debug logging:

**Advanced Logger**
```javascript
// debug-logger.js
const winston = require('winston');
const { ElasticsearchTransport } = require('winston-elasticsearch');

class DebugLogger {
    constructor(options = {}) {
        this.service = options.service || 'app';
        this.level = process.env.LOG_LEVEL || 'debug';
        this.logger = this.createLogger();
    }
    
    createLogger() {
        const formats = [
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.splat(),
            winston.format.json(),
        ];
        
        if (process.env.NODE_ENV === 'development') {
            formats.push(winston.format.colorize());
            formats.push(winston.format.printf(this.devFormat));
        }
        
        const transports = [
            new winston.transports.Console({
                level: this.level,
                handleExceptions: true,
                handleRejections: true,
            }),
        ];
        
        // Add file transport for debugging
        if (process.env.DEBUG_LOG_FILE) {
            transports.push(
                new winston.transports.File({
                    filename: process.env.DEBUG_LOG_FILE,
                    level: 'debug',
                    maxsize: 10485760, // 10MB
                    maxFiles: 5,
                })
            );
        }
        
        // Add {{CLOUD_LOG_STACK}} for production
        if (process.env.ELASTICSEARCH_URL) {
            transports.push(
                new ElasticsearchTransport({
                    level: 'info',
                    clientOpts: {
                        node: process.env.ELASTICSEARCH_URL,
                    },
                    index: `logs-${this.service}`,
                })
            );
        }
        
        return winston.createLogger({
            level: this.level,
            format: winston.format.combine(...formats),
            defaultMeta: {
                service: this.service,
                environment: process.env.NODE_ENV,
                hostname: require('os').hostname(),
                pid: process.pid,
            },
            transports,
        });
    }
    
    devFormat(info) {
        const { timestamp, level, message, ...meta } = info;
        const metaString = Object.keys(meta).length ? 
            '\n' + JSON.stringify(meta, null, 2) : '';
        
        return `${timestamp} [${level}]: ${message}${metaString}`;
    }
    
    // Debug-specific methods
    trace(message, meta = {}) {
        const stack = new Error().stack;
        this.logger.debug(message, {
            ...meta,
            trace: stack,
            timestamp: Date.now(),
        });
    }
    
    timing(label, fn) {
        const start = process.hrtime.bigint();
        const result = fn();
        const end = process.hrtime.bigint();
        const duration = Number(end - start) / 1000000; // Convert to ms
        
        this.logger.debug(`Timing: ${label}`, {
            duration,
            unit: 'ms',
        });
        
        return result;
    }
    
    memory() {
        const usage = process.memoryUsage();
        this.logger.debug('Memory usage', {
            rss: `${Math.round(usage.rss / 1024 / 1024)}MB`,
            heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)}MB`,
            heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)}MB`,
            external: `${Math.round(usage.external / 1024 / 1024)}MB`,
        });
    }
}

// Debug context manager
class DebugContext {
    constructor() {
        this.contexts = new Map();
    }
    
    create(id, metadata = {}) {
        const context = {
            id,
            startTime: Date.now(),
            metadata,
            logs: [],
            spans: [],
        };
        
        this.contexts.set(id, context);
        return context;
    }
    
    log(contextId, level, message, data = {}) {
        const context = this.contexts.get(contextId);
        if (context) {
            context.logs.push({
                timestamp: Date.now(),
                level,
                message,
                data,
            });
        }
    }
    
    export(contextId) {
        const context = this.contexts.get(contextId);
        if (!context) return null;
        
        return {
            ...context,
            duration: Date.now() - context.startTime,
            logCount: context.logs.length,
        };
    }
}
```

## Output Format

1. **Debug Configuration**: Complete IDE debugger setup for backend development
2. **Logging Framework**: Structured logging with Winston, Elasticsearch transports
3. **Troubleshooting Playbook**: Common backend debugging scenarios and solutions
4. **Debug Scripts**: Automated backend debugging utilities

Focus on creating a comprehensive backend debugging environment that enhances developer productivity and enables rapid issue resolution.

<!-- Cross-references: Related debug-trace splits -->
<!-- See also: cloud/debug-trace.md (Remote Debugging, Distributed Tracing, Production Debugging, Debug Dashboard) -->
<!-- See also: frontend/debug-trace.md (Source Map Configuration) -->
<!-- See also: general/debug-trace.md (Performance Profiling, Debug Configuration Management, IDE Integration) -->
