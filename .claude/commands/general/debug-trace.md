---
description: "Debug Configuration, Profiling & IDE Integration"
model: claude-sonnet-4-0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Debug Configuration, Profiling & IDE Integration

You are a debugging expert specializing in performance profiling, debug configuration management, and IDE integration. Configure profiling tools, centralize debug settings, and establish IDE-based debugging workflows that apply across all environments.

## Context
The user needs to set up cross-cutting debugging capabilities including performance profiling, centralized debug configuration, and IDE tooling. These are general-purpose tools that support backend, frontend, and cloud debugging workflows.

## Requirements
$ARGUMENTS

## Instructions

### 6. Performance Profiling

Implement performance profiling tools:

**Performance Profiler**
```javascript
// performance-profiler.js
const v8Profiler = require('v8-profiler-next');
const fs = require('fs');
const path = require('path');

class PerformanceProfiler {
    constructor(options = {}) {
        this.outputDir = options.outputDir || './profiles';
        this.profiles = new Map();
        
        // Ensure output directory exists
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
    }
    
    startCPUProfile(id, options = {}) {
        const title = options.title || `cpu-profile-${id}`;
        v8Profiler.startProfiling(title, true);
        
        this.profiles.set(id, {
            type: 'cpu',
            title,
            startTime: Date.now(),
        });
        
        return id;
    }
    
    stopCPUProfile(id) {
        const profileInfo = this.profiles.get(id);
        if (!profileInfo || profileInfo.type !== 'cpu') {
            throw new Error(`CPU profile ${id} not found`);
        }
        
        const profile = v8Profiler.stopProfiling(profileInfo.title);
        const duration = Date.now() - profileInfo.startTime;
        
        // Export profile
        const fileName = `${profileInfo.title}-${Date.now()}.cpuprofile`;
        const filePath = path.join(this.outputDir, fileName);
        
        profile.export((error, result) => {
            if (!error) {
                fs.writeFileSync(filePath, result);
                console.log(`CPU profile saved to ${filePath}`);
            }
            profile.delete();
        });
        
        this.profiles.delete(id);
        
        return {
            id,
            duration,
            filePath,
        };
    }
    
    takeHeapSnapshot(tag = '') {
        const fileName = `heap-${tag}-${Date.now()}.heapsnapshot`;
        const filePath = path.join(this.outputDir, fileName);
        
        const snapshot = v8Profiler.takeSnapshot();
        
        // Export snapshot
        snapshot.export((error, result) => {
            if (!error) {
                fs.writeFileSync(filePath, result);
                console.log(`Heap snapshot saved to ${filePath}`);
            }
            snapshot.delete();
        });
        
        return filePath;
    }
    
    measureFunction(fn, name = 'anonymous') {
        const measurements = {
            name,
            executions: 0,
            totalTime: 0,
            minTime: Infinity,
            maxTime: 0,
            avgTime: 0,
            lastExecution: null,
        };
        
        return new Proxy(fn, {
            apply(target, thisArg, args) {
                const start = process.hrtime.bigint();
                
                try {
                    const result = target.apply(thisArg, args);
                    
                    if (result instanceof Promise) {
                        return result.finally(() => {
                            this.recordExecution(start);
                        });
                    }
                    
                    this.recordExecution(start);
                    return result;
                } catch (error) {
                    this.recordExecution(start);
                    throw error;
                }
            },
            
            recordExecution(start) {
                const end = process.hrtime.bigint();
                const duration = Number(end - start) / 1000000; // Convert to ms
                
                measurements.executions++;
                measurements.totalTime += duration;
                measurements.minTime = Math.min(measurements.minTime, duration);
                measurements.maxTime = Math.max(measurements.maxTime, duration);
                measurements.avgTime = measurements.totalTime / measurements.executions;
                measurements.lastExecution = new Date();
                
                // Log slow executions
                if (duration > 100) {
                    console.warn(`Slow function execution: ${name} took ${duration}ms`);
                }
            },
            
            get(target, prop) {
                if (prop === 'measurements') {
                    return measurements;
                }
                return target[prop];
            },
        });
    }
}

// Memory leak detector
class MemoryLeakDetector {
    constructor() {
        this.snapshots = [];
        this.threshold = 50 * 1024 * 1024; // 50MB
    }
    
    start(interval = 60000) {
        this.interval = setInterval(() => {
            this.checkMemory();
        }, interval);
    }
    
    checkMemory() {
        const usage = process.memoryUsage();
        const snapshot = {
            timestamp: Date.now(),
            heapUsed: usage.heapUsed,
            external: usage.external,
            rss: usage.rss,
        };
        
        this.snapshots.push(snapshot);
        
        // Keep only last 10 snapshots
        if (this.snapshots.length > 10) {
            this.snapshots.shift();
        }
        
        // Check for memory leak pattern
        if (this.snapshots.length >= 5) {
            const trend = this.calculateTrend();
            if (trend.increasing && trend.delta > this.threshold) {
                console.error('Potential memory leak detected!', {
                    trend,
                    current: snapshot,
                });
                
                // Take heap snapshot for analysis
                const profiler = new PerformanceProfiler();
                profiler.takeHeapSnapshot('leak-detection');
            }
        }
    }
    
    calculateTrend() {
        const recent = this.snapshots.slice(-5);
        const first = recent[0];
        const last = recent[recent.length - 1];
        
        const delta = last.heapUsed - first.heapUsed;
        const increasing = recent.every((s, i) => 
            i === 0 || s.heapUsed > recent[i - 1].heapUsed
        );
        
        return {
            increasing,
            delta,
            rate: delta / (last.timestamp - first.timestamp) * 1000 * 60, // MB per minute
        };
    }
}
```

### 7. Debug Configuration Management

Centralize debug configurations:

**Debug Configuration**
```javascript
// debug-config.js
class DebugConfiguration {
    constructor() {
        this.config = {
            // Debug levels
            levels: {
                error: 0,
                warn: 1,
                info: 2,
                debug: 3,
                trace: 4,
            },
            
            // Feature flags
            features: {
                remoteDebugging: process.env.ENABLE_REMOTE_DEBUG === 'true',
                tracing: process.env.ENABLE_TRACING === 'true',
                profiling: process.env.ENABLE_PROFILING === 'true',
                memoryMonitoring: process.env.ENABLE_MEMORY_MONITORING === 'true',
            },
            
            // Debug endpoints
            endpoints: {
                jaeger: process.env.JAEGER_ENDPOINT || 'http://localhost:14268',
                elasticsearch: process.env.ELASTICSEARCH_URL || 'http://localhost:9200',
                sentry: process.env.SENTRY_DSN,
            },
            
            // Sampling rates
            sampling: {
                traces: parseFloat(process.env.TRACE_SAMPLING_RATE || '0.1'),
                profiles: parseFloat(process.env.PROFILE_SAMPLING_RATE || '0.01'),
                logs: parseFloat(process.env.LOG_SAMPLING_RATE || '1.0'),
            },
        };
    }
    
    isEnabled(feature) {
        return this.config.features[feature] || false;
    }
    
    getLevel() {
        const level = process.env.DEBUG_LEVEL || 'info';
        return this.config.levels[level] || 2;
    }
    
    shouldSample(type) {
        const rate = this.config.sampling[type] || 1.0;
        return Math.random() < rate;
    }
}

// Debug middleware factory
class DebugMiddlewareFactory {
    static create(app, config) {
        const middlewares = [];
        
        if (config.isEnabled('tracing')) {
            const tracingMiddleware = new TracingMiddleware();
            middlewares.push(tracingMiddleware.express());
        }
        
        if (config.isEnabled('profiling')) {
            middlewares.push(this.profilingMiddleware());
        }
        
        if (config.isEnabled('memoryMonitoring')) {
            const detector = new MemoryLeakDetector();
            detector.start();
        }
        
        // Debug routes
        if (process.env.NODE_ENV === 'development') {
            app.get('/debug/heap', (req, res) => {
                const profiler = new PerformanceProfiler();
                const path = profiler.takeHeapSnapshot('manual');
                res.json({ heapSnapshot: path });
            });
            
            app.get('/debug/profile', async (req, res) => {
                const profiler = new PerformanceProfiler();
                const id = profiler.startCPUProfile('manual');
                
                setTimeout(() => {
                    const result = profiler.stopCPUProfile(id);
                    res.json(result);
                }, 10000);
            });
            
            app.get('/debug/metrics', (req, res) => {
                res.json({
                    memory: process.memoryUsage(),
                    cpu: process.cpuUsage(),
                    uptime: process.uptime(),
                });
            });
        }
        
        return middlewares;
    }
    
    static profilingMiddleware() {
        const profiler = new PerformanceProfiler();
        
        return (req, res, next) => {
            if (Math.random() < 0.01) { // 1% sampling
                const id = profiler.startCPUProfile(`request-${Date.now()}`);
                
                res.on('finish', () => {
                    profiler.stopCPUProfile(id);
                });
            }
            
            next();
        };
    }
}
```

### 10. IDE Integration

Configure IDE debugging features:

**IDE Debug Extensions**
```json
// .vscode/extensions.json
{
    "recommendations": [
        "ms-vscode.vscode-js-debug",
        "msjsdiag.debugger-for-chrome",
        "ms-vscode.vscode-typescript-tslint-plugin",
        "dbaeumer.vscode-eslint",
        "ms-azuretools.vscode-docker",
        "humao.rest-client",
        "eamodio.gitlens",
        "usernamehw.errorlens",
        "wayou.vscode-todo-highlight",
        "formulahendry.code-runner"
    ]
}

// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Debug Server",
            "type": "npm",
            "script": "debug",
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            }
        },
        {
            "label": "Profile Application",
            "type": "shell",
            "command": "node --inspect-brk --cpu-prof --cpu-prof-dir=./profiles ${workspaceFolder}/src/index.js",
            "problemMatcher": []
        },
        {
            "label": "Memory Snapshot",
            "type": "shell",
            "command": "node --inspect --expose-gc ${workspaceFolder}/scripts/heap-snapshot.js",
            "problemMatcher": []
        }
    ]
}
```

## Output Format

1. **Performance Profiling**: CPU profiling, heap snapshots, function measurement, memory leak detection
2. **Debug Configuration**: Centralized config management with feature flags and sampling rates
3. **IDE Integration**: VS Code extensions, tasks, and debug workflows
4. **Performance Baselines**: Metrics for comparison
5. **Documentation**: Team debugging guidelines

Focus on creating cross-cutting debugging tools that enhance developer productivity across all environments.

## Related Templates

<!-- All debug-trace domain splits -->
<!-- See: backend/debug-trace.md (Development Environment Debugging, Debug Logging Framework) -->
<!-- See: frontend/debug-trace.md (Source Map Configuration) -->
<!-- See: cloud/debug-trace.md (Remote Debugging, Distributed Tracing, Production Debugging, Debug Dashboard) -->
