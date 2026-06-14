---
model: claude-sonnet-4-0
description: "Error Alerting, Monitoring & Dashboards"
complexity: advanced
priority: high
tags: [error-handling, monitoring, cloud, alerting]
depends_on: []
chains_to: []
skip_if: [no_cloud]
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Error Alerting, Monitoring & Dashboards

You are an error alerting and monitoring expert specializing in implementing comprehensive cloud observability solutions. Set up intelligent alerting, performance impact tracking, and real-time error dashboards to ensure teams can quickly detect and respond to production issues.

## Context
The user needs to implement or improve error alerting, performance monitoring, and error dashboards. Focus on intelligent alerting rules, anomaly detection, performance impact analysis, and real-time visualization.

## Requirements
$ARGUMENTS

## Instructions

### 1. Error Alerting Configuration

Set up intelligent alerting:

**Alert Manager**
```python
# alert_manager.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio

@dataclass
class AlertRule:
    name: str
    condition: str
    threshold: float
    window: timedelta
    severity: str
    channels: List[str]
    cooldown: timedelta = timedelta(minutes=15)

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.rules = self._load_rules()
        self.alert_history = {}
        self.channels = self._setup_channels()
    
    def _load_rules(self):
        """Load alert rules from configuration"""
        return [
            AlertRule(
                name="High Error Rate",
                condition="error_rate",
                threshold=0.05,  # 5% error rate
                window=timedelta(minutes=5),
                severity="critical",
                channels=["slack", "pagerduty"]
            ),
            AlertRule(
                name="Response Time Degradation",
                condition="response_time_p95",
                threshold=1000,  # 1 second
                window=timedelta(minutes=10),
                severity="warning",
                channels=["slack"]
            ),
            AlertRule(
                name="Memory Usage Critical",
                condition="memory_usage_percent",
                threshold=90,
                window=timedelta(minutes=5),
                severity="critical",
                channels=["slack", "pagerduty"]
            ),
            AlertRule(
                name="Disk Space Low",
                condition="disk_free_percent",
                threshold=10,
                window=timedelta(minutes=15),
                severity="warning",
                channels=["slack", "email"]
            )
        ]
    
    async def evaluate_rules(self, metrics: Dict):
        """Evaluate all alert rules against current metrics"""
        for rule in self.rules:
            if await self._should_alert(rule, metrics):
                await self._send_alert(rule, metrics)
    
    async def _should_alert(self, rule: AlertRule, metrics: Dict) -> bool:
        """Check if alert should be triggered"""
        # Check if metric exists
        if rule.condition not in metrics:
            return False
        
        # Check threshold
        value = metrics[rule.condition]
        if not self._check_threshold(value, rule.threshold, rule.condition):
            return False
        
        # Check cooldown
        last_alert = self.alert_history.get(rule.name)
        if last_alert and datetime.now() - last_alert < rule.cooldown:
            return False
        
        return True
    
    async def _send_alert(self, rule: AlertRule, metrics: Dict):
        """Send alert through configured channels"""
        alert_data = {
            "rule": rule.name,
            "severity": rule.severity,
            "value": metrics[rule.condition],
            "threshold": rule.threshold,
            "timestamp": datetime.now().isoformat(),
            "environment": self.config.environment,
            "service": self.config.service
        }
        
        # Send to all channels
        tasks = []
        for channel_name in rule.channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                tasks.append(channel.send(alert_data))
        
        await asyncio.gather(*tasks)
        
        # Update alert history
        self.alert_history[rule.name] = datetime.now()

# Alert channels
class SlackAlertChannel:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    async def send(self, alert_data):
        """Send alert to Slack"""
        color = {
            "critical": "danger",
            "warning": "warning",
            "info": "good"
        }.get(alert_data["severity"], "danger")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 {alert_data['rule']}",
                "fields": [
                    {
                        "title": "Severity",
                        "value": alert_data["severity"].upper(),
                        "short": True
                    },
                    {
                        "title": "Environment",
                        "value": alert_data["environment"],
                        "short": True
                    },
                    {
                        "title": "Current Value",
                        "value": str(alert_data["value"]),
                        "short": True
                    },
                    {
                        "title": "Threshold",
                        "value": str(alert_data["threshold"]),
                        "short": True
                    }
                ],
                "footer": alert_data["service"],
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        # Send to Slack
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=payload)
```

### 2. Performance Impact Tracking

Monitor performance impact of errors:

**Performance Monitor**
```typescript
// performance-monitor.ts
interface PerformanceMetrics {
    responseTime: number;
    errorRate: number;
    throughput: number;
    apdex: number;
    resourceUsage: {
        cpu: number;
        memory: number;
        disk: number;
    };
}

class PerformanceMonitor {
    private metrics: Map<string, PerformanceMetrics[]> = new Map();
    private intervals: Map<string, NodeJS.Timer> = new Map();
    
    startMonitoring(service: string, interval: number = 60000) {
        const timer = setInterval(() => {
            this.collectMetrics(service);
        }, interval);
        
        this.intervals.set(service, timer);
    }
    
    private async collectMetrics(service: string) {
        const metrics: PerformanceMetrics = {
            responseTime: await this.getResponseTime(service),
            errorRate: await this.getErrorRate(service),
            throughput: await this.getThroughput(service),
            apdex: await this.calculateApdex(service),
            resourceUsage: await this.getResourceUsage()
        };
        
        // Store metrics
        if (!this.metrics.has(service)) {
            this.metrics.set(service, []);
        }
        
        const serviceMetrics = this.metrics.get(service)!;
        serviceMetrics.push(metrics);
        
        // Keep only last 24 hours
        const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
        const filtered = serviceMetrics.filter(m => m.timestamp > dayAgo);
        this.metrics.set(service, filtered);
        
        // Check for anomalies
        this.detectAnomalies(service, metrics);
    }
    
    private detectAnomalies(service: string, current: PerformanceMetrics) {
        const history = this.metrics.get(service) || [];
        if (history.length < 10) return; // Need history for comparison
        
        // Calculate baselines
        const baseline = this.calculateBaseline(history.slice(-60)); // Last hour
        
        // Check for anomalies
        const anomalies = [];
        
        if (current.responseTime > baseline.responseTime * 2) {
            anomalies.push({
                type: 'response_time_spike',
                severity: 'warning',
                value: current.responseTime,
                baseline: baseline.responseTime
            });
        }
        
        if (current.errorRate > baseline.errorRate + 0.05) {
            anomalies.push({
                type: 'error_rate_increase',
                severity: 'critical',
                value: current.errorRate,
                baseline: baseline.errorRate
            });
        }
        
        if (anomalies.length > 0) {
            this.reportAnomalies(service, anomalies);
        }
    }
    
    private calculateBaseline(history: PerformanceMetrics[]) {
        const sum = history.reduce((acc, m) => ({
            responseTime: acc.responseTime + m.responseTime,
            errorRate: acc.errorRate + m.errorRate,
            throughput: acc.throughput + m.throughput,
            apdex: acc.apdex + m.apdex
        }), {
            responseTime: 0,
            errorRate: 0,
            throughput: 0,
            apdex: 0
        });
        
        return {
            responseTime: sum.responseTime / history.length,
            errorRate: sum.errorRate / history.length,
            throughput: sum.throughput / history.length,
            apdex: sum.apdex / history.length
        };
    }
    
    async calculateApdex(service: string, threshold: number = 500) {
        // Apdex = (Satisfied + Tolerating/2) / Total
        const satisfied = await this.countRequests(service, 0, threshold);
        const tolerating = await this.countRequests(service, threshold, threshold * 4);
        const total = await this.getTotalRequests(service);
        
        if (total === 0) return 1;
        
        return (satisfied + tolerating / 2) / total;
    }
}
```

### 3. Error Dashboard

Create comprehensive error dashboard:

**Dashboard Component**
```typescript
// error-dashboard.tsx
import {{FE_FRAMEWORK}} from 'react';
import { LineChart, BarChart, PieChart } from 'recharts';

const ErrorDashboard: {{FE_FRAMEWORK}}.FC = () => {
    const [metrics, setMetrics] = useState<DashboardMetrics>();
    const [timeRange, setTimeRange] = useState('1h');
    
    useEffect(() => {
        const fetchMetrics = async () => {
            const data = await getErrorMetrics(timeRange);
            setMetrics(data);
        };
        
        fetchMetrics();
        const interval = setInterval(fetchMetrics, 30000); // Update every 30s
        
        return () => clearInterval(interval);
    }, [timeRange]);
    
    if (!metrics) return <Loading />;
    
    return (
        <div className="error-dashboard">
            <Header>
                <h1>Error Tracking Dashboard</h1>
                <TimeRangeSelector
                    value={timeRange}
                    onChange={setTimeRange}
                    options={['1h', '6h', '24h', '7d', '30d']}
                />
            </Header>
            
            <MetricCards>
                <MetricCard
                    title="Error Rate"
                    value={`${(metrics.errorRate * 100).toFixed(2)}%`}
                    trend={metrics.errorRateTrend}
                    status={metrics.errorRate > 0.05 ? 'critical' : 'ok'}
                />
                <MetricCard
                    title="Total Errors"
                    value={metrics.totalErrors.toLocaleString()}
                    trend={metrics.errorsTrend}
                />
                <MetricCard
                    title="Affected Users"
                    value={metrics.affectedUsers.toLocaleString()}
                    trend={metrics.usersTrend}
                />
                <MetricCard
                    title="MTTR"
                    value={formatDuration(metrics.mttr)}
                    trend={metrics.mttrTrend}
                />
            </MetricCards>
            
            <ChartGrid>
                <ChartCard title="Error Trend">
                    <LineChart data={metrics.errorTrend}>
                        <Line
                            type="monotone"
                            dataKey="errors"
                            stroke="#ff6b6b"
                            strokeWidth={2}
                        />
                        <Line
                            type="monotone"
                            dataKey="warnings"
                            stroke="#ffd93d"
                            strokeWidth={2}
                        />
                    </LineChart>
                </ChartCard>
                
                <ChartCard title="Error Distribution">
                    <PieChart data={metrics.errorDistribution}>
                        <Pie
                            dataKey="count"
                            nameKey="type"
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                        />
                    </PieChart>
                </ChartCard>
                
                <ChartCard title="Top Errors">
                    <BarChart data={metrics.topErrors}>
                        <Bar dataKey="count" fill="#ff6b6b" />
                    </BarChart>
                </ChartCard>
                
                <ChartCard title="Error Heatmap">
                    <ErrorHeatmap data={metrics.errorHeatmap} />
                </ChartCard>
            </ChartGrid>
            
            <ErrorList>
                <h2>Recent Errors</h2>
                <ErrorTable
                    errors={metrics.recentErrors}
                    onErrorClick={handleErrorClick}
                />
            </ErrorList>
            
            <AlertsSection>
                <h2>Active Alerts</h2>
                <AlertsList alerts={metrics.activeAlerts} />
            </AlertsSection>
        </div>
    );
};

// Real-time error stream
const ErrorStream: {{FE_FRAMEWORK}}.FC = () => {
    const [errors, setErrors] = useState<ErrorEvent[]>([]);
    
    useEffect(() => {
        const eventSource = new EventSource('/api/errors/stream');
        
        eventSource.onmessage = (event) => {
            const error = JSON.parse(event.data);
            setErrors(prev => [error, ...prev].slice(0, 100));
        };
        
        return () => eventSource.close();
    }, []);
    
    return (
        <div className="error-stream">
            <h3>Live Error Stream</h3>
            <div className="stream-container">
                {errors.map((error, index) => (
                    <ErrorStreamItem
                        key={error.id}
                        error={error}
                        isNew={index === 0}
                    />
                ))}
            </div>
        </div>
    );
};
```

## Output Format

1. **Alert Rules**: Intelligent alerting configuration
2. **Performance Monitoring**: Anomaly detection and impact tracking
3. **Dashboard Setup**: Real-time error monitoring dashboard
4. **Documentation**: Implementation and troubleshooting guide

Focus on providing intelligent alerting, comprehensive performance monitoring, and real-time error visibility through dashboards.

<!-- Cross-reference: For backend error tracking, structured logging, error grouping, and recovery strategies, see backend/error-trace.md -->
