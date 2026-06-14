---
model: claude-sonnet-4-0
description: "Migration Planning, Rollback & Orchestration"
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Code Migration Orchestration

You are a code migration orchestrator specializing in assessment, planning, rollback strategies, automation tooling, and progress monitoring. Generate comprehensive migration plans, automated tooling, and ensure smooth transitions with minimal disruption.

## Context
The user needs to plan and orchestrate a code migration. This template covers the shared concerns that apply to all migrations: assessment, planning, rollback, automation, and monitoring. For domain-specific migration logic, see the related templates below.

## Requirements
$ARGUMENTS

## Instructions

### 1. Migration Assessment

Analyze the current codebase and migration requirements:

**Migration Analyzer**
```python
import os
import json
import ast
import re
from pathlib import Path
from collections import defaultdict

class MigrationAnalyzer:
    def __init__(self, source_path, target_tech):
        self.source_path = Path(source_path)
        self.target_tech = target_tech
        self.analysis = defaultdict(dict)
    
    def analyze_migration(self):
        """
        Comprehensive migration analysis
        """
        self.analysis['source'] = self._analyze_source()
        self.analysis['complexity'] = self._assess_complexity()
        self.analysis['dependencies'] = self._analyze_dependencies()
        self.analysis['risks'] = self._identify_risks()
        self.analysis['effort'] = self._estimate_effort()
        self.analysis['strategy'] = self._recommend_strategy()
        
        return self.analysis
    
    def _analyze_source(self):
        """Analyze source codebase characteristics"""
        stats = {
            'files': 0,
            'lines': 0,
            'components': 0,
            'patterns': [],
            'frameworks': set(),
            'languages': defaultdict(int)
        }
        
        for file_path in self.source_path.rglob('*'):
            if file_path.is_file() and not self._is_ignored(file_path):
                stats['files'] += 1
                ext = file_path.suffix
                stats['languages'][ext] += 1
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    stats['lines'] += len(content.splitlines())
                    
                    # Detect frameworks and patterns
                    self._detect_patterns(content, stats)
        
        return stats
    
    def _assess_complexity(self):
        """Assess migration complexity"""
        factors = {
            'size': self._calculate_size_complexity(),
            'architectural': self._calculate_architectural_complexity(),
            'dependency': self._calculate_dependency_complexity(),
            'business_logic': self._calculate_logic_complexity(),
            'data': self._calculate_data_complexity()
        }
        
        overall = sum(factors.values()) / len(factors)
        
        return {
            'factors': factors,
            'overall': overall,
            'level': self._get_complexity_level(overall)
        }
    
    def _identify_risks(self):
        """Identify migration risks"""
        risks = []
        
        # Check for high-risk patterns
        risk_patterns = {
            'global_state': {
                'pattern': r'(global|window)\.\w+\s*=',
                'severity': 'high',
                'description': 'Global state management needs careful migration'
            },
            'direct_dom': {
                'pattern': r'document\.(getElementById|querySelector)',
                'severity': 'medium',
                'description': 'Direct DOM manipulation needs framework adaptation'
            },
            'async_patterns': {
                'pattern': r'(callback|setTimeout|setInterval)',
                'severity': 'medium',
                'description': 'Async patterns may need modernization'
            },
            'deprecated_apis': {
                'pattern': r'(componentWillMount|componentWillReceiveProps)',
                'severity': 'high',
                'description': 'Deprecated APIs need replacement'
            }
        }
        
        for risk_name, risk_info in risk_patterns.items():
            occurrences = self._count_pattern_occurrences(risk_info['pattern'])
            if occurrences > 0:
                risks.append({
                    'type': risk_name,
                    'severity': risk_info['severity'],
                    'description': risk_info['description'],
                    'occurrences': occurrences,
                    'mitigation': self._suggest_mitigation(risk_name)
                })
        
        return sorted(risks, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']])
```

### 2. Migration Planning

Create detailed migration plans:

**Migration Planner**
```python
class MigrationPlanner:
    def create_migration_plan(self, analysis):
        """
        Create comprehensive migration plan
        """
        plan = {
            'phases': self._define_phases(analysis),
            'timeline': self._estimate_timeline(analysis),
            'resources': self._calculate_resources(analysis),
            'milestones': self._define_milestones(analysis),
            'success_criteria': self._define_success_criteria()
        }
        
        return self._format_plan(plan)
    
    def _define_phases(self, analysis):
        """Define migration phases"""
        complexity = analysis['complexity']['overall']
        
        if complexity < 3:
            # Simple migration
            return [
                {
                    'name': 'Preparation',
                    'duration': '1 week',
                    'tasks': [
                        'Setup new project structure',
                        'Install dependencies',
                        'Configure build tools',
                        'Setup testing framework'
                    ]
                },
                {
                    'name': 'Core Migration',
                    'duration': '2-3 weeks',
                    'tasks': [
                        'Migrate utility functions',
                        'Port components/modules',
                        'Update data models',
                        'Migrate business logic'
                    ]
                },
                {
                    'name': 'Testing & Refinement',
                    'duration': '1 week',
                    'tasks': [
                        'Unit testing',
                        'Integration testing',
                        'Performance testing',
                        'Bug fixes'
                    ]
                }
            ]
        else:
            # Complex migration
            return [
                {
                    'name': 'Phase 0: Foundation',
                    'duration': '2 weeks',
                    'tasks': [
                        'Architecture design',
                        'Proof of concept',
                        'Tool selection',
                        'Team training'
                    ]
                },
                {
                    'name': 'Phase 1: Infrastructure',
                    'duration': '3 weeks',
                    'tasks': [
                        'Setup build pipeline',
                        'Configure development environment',
                        'Implement core abstractions',
                        'Setup automated testing'
                    ]
                },
                {
                    'name': 'Phase 2: Incremental Migration',
                    'duration': '6-8 weeks',
                    'tasks': [
                        'Migrate shared utilities',
                        'Port feature modules',
                        'Implement adapters/bridges',
                        'Maintain dual runtime'
                    ]
                },
                {
                    'name': 'Phase 3: Cutover',
                    'duration': '2 weeks',
                    'tasks': [
                        'Complete remaining migrations',
                        'Remove legacy code',
                        'Performance optimization',
                        'Final testing'
                    ]
                }
            ]
    
    def _format_plan(self, plan):
        """Format migration plan as markdown"""
        output = "# Migration Plan\n\n"
        
        # Executive Summary
        output += "## Executive Summary\n\n"
        output += f"- **Total Duration**: {plan['timeline']['total']}\n"
        output += f"- **Team Size**: {plan['resources']['team_size']}\n"
        output += f"- **Risk Level**: {plan['timeline']['risk_buffer']}\n\n"
        
        # Phases
        output += "## Migration Phases\n\n"
        for i, phase in enumerate(plan['phases']):
            output += f"### {phase['name']}\n"
            output += f"**Duration**: {phase['duration']}\n\n"
            output += "**Tasks**:\n"
            for task in phase['tasks']:
                output += f"- {task}\n"
            output += "\n"
        
        # Milestones
        output += "## Key Milestones\n\n"
        for milestone in plan['milestones']:
            output += f"- **{milestone['name']}**: {milestone['criteria']}\n"
        
        return output
```

### 8. Rollback Planning

Implement safe rollback strategies:

```python
class RollbackManager:
    def create_rollback_plan(self, migration_type):
        """Create comprehensive rollback plan"""
        plan = {
            'triggers': self.define_rollback_triggers(),
            'procedures': self.define_rollback_procedures(migration_type),
            'verification': self.define_verification_steps(),
            'communication': self.define_communication_plan()
        }
        
        return self.format_rollback_plan(plan)
    
    def define_rollback_triggers(self):
        """Define conditions that trigger rollback"""
        return [
            {
                'condition': 'Critical functionality broken',
                'threshold': 'Any P0 feature non-functional',
                'detection': 'Automated monitoring + user reports'
            },
            {
                'condition': 'Performance degradation',
                'threshold': '>50% increase in response time',
                'detection': 'APM metrics'
            },
            {
                'condition': 'Data corruption',
                'threshold': 'Any data integrity issues',
                'detection': 'Data validation checks'
            },
            {
                'condition': 'High error rate',
                'threshold': '>5% error rate increase',
                'detection': 'Error tracking system'
            }
        ]
    
    def define_rollback_procedures(self, migration_type):
        """Define step-by-step rollback procedures"""
        if migration_type == 'blue_green':
            return self._blue_green_rollback()
        elif migration_type == 'canary':
            return self._canary_rollback()
        elif migration_type == 'feature_flag':
            return self._feature_flag_rollback()
        else:
            return self._standard_rollback()
    
    def _blue_green_rollback(self):
        return [
            "1. Verify green environment is problematic",
            "2. Update load balancer to route 100% to blue",
            "3. Monitor blue environment stability",
            "4. Notify stakeholders of rollback",
            "5. Begin root cause analysis",
            "6. Keep green environment for debugging"
        ]
```

### 9. Migration Automation

Create automated migration tools:

```python
def create_migration_cli():
    """Generate CLI tool for migration"""
    return '''
#!/usr/bin/env python3
import click
import json
from pathlib import Path

@click.group()
def cli():
    """Code Migration Tool"""
    pass

@cli.command()
@click.option('--source', required=True, help='Source directory')
@click.option('--target', required=True, help='Target technology')
@click.option('--output', default='migration-plan.json', help='Output file')
def analyze(source, target, output):
    """Analyze codebase for migration"""
    analyzer = MigrationAnalyzer(source, target)
    analysis = analyzer.analyze_migration()
    
    with open(output, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    click.echo(f"Analysis complete. Results saved to {output}")

@cli.command()
@click.option('--plan', required=True, help='Migration plan file')
@click.option('--phase', help='Specific phase to execute')
@click.option('--dry-run', is_flag=True, help='Simulate migration')
def migrate(plan, phase, dry_run):
    """Execute migration based on plan"""
    with open(plan) as f:
        migration_plan = json.load(f)
    
    migrator = CodeMigrator(migration_plan)
    
    if dry_run:
        click.echo("Running migration in dry-run mode...")
        results = migrator.dry_run(phase)
    else:
        click.echo("Executing migration...")
        results = migrator.execute(phase)
    
    # Display results
    for result in results:
        status = "✓" if result['success'] else "✗"
        click.echo(f"{status} {result['task']}: {result['message']}")

@cli.command()
@click.option('--original', required=True, help='Original codebase')
@click.option('--migrated', required=True, help='Migrated codebase')
def test(original, migrated):
    """Test migration results"""
    tester = MigrationTester(original, migrated)
    results = tester.run_comparison_tests()
    
    # Display test results
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    
    click.echo(f"\\nTest Results: {passed}/{total} passed")
    
    for result in results:
        if result['status'] == 'FAIL':
            click.echo(f"\\n❌ {result['test']}")
            click.echo(f"   {result['details']}")

if __name__ == '__main__':
    cli()
'''
```

### 10. Progress Monitoring

Track migration progress:

```python
class MigrationMonitor:
    def __init__(self, migration_id):
        self.migration_id = migration_id
        self.metrics = defaultdict(list)
        self.checkpoints = []
    
    def create_dashboard(self):
        """Create migration monitoring dashboard"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Migration Dashboard - {self.migration_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card {{
            background: #f5f5f5;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: #4CAF50;
            transition: width 0.5s;
        }}
    </style>
</head>
<body>
    <h1>Migration Progress Dashboard</h1>
    
    <div class="metric-card">
        <h2>Overall Progress</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {self.calculate_progress()}%"></div>
        </div>
        <p>{self.calculate_progress()}% Complete</p>
    </div>
    
    <div class="metric-card">
        <h2>Phase Status</h2>
        <canvas id="phaseChart"></canvas>
    </div>
    
    <div class="metric-card">
        <h2>Migration Metrics</h2>
        <canvas id="metricsChart"></canvas>
    </div>
    
    <div class="metric-card">
        <h2>Recent Activities</h2>
        <ul id="activities">
            {self.format_recent_activities()}
        </ul>
    </div>
    
    <script>
        // Update dashboard every 30 seconds
        setInterval(() => location.reload(), 30000);
        
        // Phase chart
        new Chart(document.getElementById('phaseChart'), {{
            type: 'doughnut',
            data: {self.get_phase_chart_data()}
        }});
        
        // Metrics chart
        new Chart(document.getElementById('metricsChart'), {{
            type: 'line',
            data: {self.get_metrics_chart_data()}
        }});
    </script>
</body>
</html>
"""
```

## Output Format

1. **Migration Analysis**: Comprehensive analysis of source codebase
2. **Risk Assessment**: Identified risks with mitigation strategies
3. **Migration Plan**: Phased approach with timeline and milestones
4. **Rollback Plan**: Detailed procedures for safe rollback
5. **Automation Tooling**: CLI tools for executing and testing migrations
6. **Progress Tracking**: Real-time migration monitoring
7. **Documentation**: Migration guide and runbooks

Focus on minimizing disruption, maintaining functionality, and providing clear paths for successful code migration with comprehensive testing and rollback strategies.

## Related Templates

<!-- For domain-specific migration logic, use the following templates: -->
<!-- - backend/code-migrate.md : Language upgrades (Python 2→3, JS→TS), API migrations (REST→GraphQL), Database migrations (SQL→NoSQL) -->
<!-- - frontend/code-migrate.md : Framework migrations (React→Vue, Angular→React, etc.) -->
