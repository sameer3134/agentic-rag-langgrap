---
model: claude-sonnet-4-0
description: "Frontend Framework Migration"
complexity: advanced
priority: medium
tags: ["migration", "frontend", "components"]
depends_on: ["general/research_codebase"]
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Frontend Framework Migration

You are a frontend migration expert specializing in framework-to-framework transitions (React to Vue, Angular to React, etc.). Generate comprehensive component migration scripts, template converters, and ensure smooth UI transitions with minimal disruption.

## Context
The user needs to migrate a frontend codebase from one framework to another. Focus on preserving component structure, user interactions, styling, and providing clear migration paths with rollback strategies.

## Requirements
$ARGUMENTS

## Instructions

### Migration Assessment (Overview)

Before migrating, analyze the frontend codebase for component patterns, state management, routing, and framework-specific APIs. Use the full assessment tooling from [`general/code-migrate.md`](../general/code-migrate.md) for a comprehensive analysis including complexity scoring, risk identification, and effort estimation.

### 3. Framework Migrations

Handle specific framework migrations:

**{{FE_FRAMEWORK}} to {{FE_FRAMEWORK}} Migration**
```javascript
class ReactToVueMigrator {
    migrateComponent(reactComponent) {
        // Parse React component
        const ast = parseReactComponent(reactComponent);
        
        // Extract component structure
        const componentInfo = {
            name: this.extractComponentName(ast),
            props: this.extractProps(ast),
            state: this.extractState(ast),
            methods: this.extractMethods(ast),
            lifecycle: this.extractLifecycle(ast),
            render: this.extractRender(ast)
        };
        
        // Generate Vue component
        return this.generateVueComponent(componentInfo);
    }
    
    generateVueComponent(info) {
        return `
<template>
${this.convertJSXToTemplate(info.render)}
</template>

<script>
export default {
    name: '${info.name}',
    props: ${this.convertProps(info.props)},
    data() {
        return ${this.convertState(info.state)}
    },
    methods: ${this.convertMethods(info.methods)},
    ${this.convertLifecycle(info.lifecycle)}
}
</script>

<style scoped>
/* Component styles */
</style>
`;
    }
    
    convertJSXToTemplate(jsx) {
        // Convert JSX to Vue template syntax
        let template = jsx;
        
        // Convert className to class
        template = template.replace(/className=/g, 'class=');
        
        // Convert onClick to @click
        template = template.replace(/onClick={/g, '@click="');
        template = template.replace(/on(\w+)={this\.(\w+)}/g, '@$1="$2"');
        
        // Convert conditional rendering
        template = template.replace(/{(\w+) && (.+?)}/g, '<template v-if="$1">$2</template>');
        template = template.replace(/{(\w+) \? (.+?) : (.+?)}/g, 
            '<template v-if="$1">$2</template><template v-else>$3</template>');
        
        // Convert map iterations
        template = template.replace(
            /{(\w+)\.map\(\((\w+), (\w+)\) => (.+?)\)}/g,
            '<template v-for="($2, $3) in $1" :key="$3">$4</template>'
        );
        
        return template;
    }
    
    convertLifecycle(lifecycle) {
        const vueLifecycle = {
            'componentDidMount': 'mounted',
            'componentDidUpdate': 'updated',
            'componentWillUnmount': 'beforeDestroy',
            'getDerivedStateFromProps': 'computed'
        };
        
        let result = '';
        for (const [reactHook, vueHook] of Object.entries(vueLifecycle)) {
            if (lifecycle[reactHook]) {
                result += `${vueHook}() ${lifecycle[reactHook].body},\n`;
            }
        }
        
        return result;
    }
}
```

### 7. Frontend Testing Strategy

Ensure frontend migration correctness with UI equivalence, user flow, and rendering tests:

```python
class FrontendMigrationTester:
    def __init__(self, original_app, migrated_app):
        self.original = original_app
        self.migrated = migrated_app
        self.test_results = []
    
    def run_comparison_tests(self):
        """Run side-by-side comparison tests for frontend systems"""
        test_suites = [
            self.test_functionality,
            self.test_user_flows,
            self.test_performance
        ]
        
        for suite in test_suites:
            results = suite()
            self.test_results.extend(results)
        
        return self.generate_report()
    
    def test_functionality(self):
        """Test functional equivalence of UI components"""
        results = []
        
        test_cases = self.generate_test_cases()
        
        for test in test_cases:
            original_result = self.execute_on_original(test)
            migrated_result = self.execute_on_migrated(test)
            
            comparison = self.compare_results(
                original_result, 
                migrated_result
            )
            
            results.append({
                'test': test['name'],
                'status': 'PASS' if comparison['equivalent'] else 'FAIL',
                'details': comparison['details']
            })
        
        return results
    
    def test_user_flows(self):
        """Verify critical user flows are preserved after migration"""
        results = []
        
        test_cases = self.generate_test_cases()
        
        for test in test_cases:
            original_result = self.execute_on_original(test)
            migrated_result = self.execute_on_migrated(test)
            
            comparison = self.compare_results(
                original_result,
                migrated_result
            )
            
            results.append({
                'test': test['name'],
                'status': 'PASS' if comparison['equivalent'] else 'FAIL',
                'details': comparison['details']
            })
        
        return results
    
    def test_performance(self):
        """Compare frontend performance metrics (render time, bundle size, etc.)"""
        metrics = ['response_time', 'throughput', 'cpu_usage', 'memory_usage']
        results = []
        
        for metric in metrics:
            original_perf = self.measure_performance(self.original, metric)
            migrated_perf = self.measure_performance(self.migrated, metric)
            
            regression = ((migrated_perf - original_perf) / original_perf) * 100
            
            results.append({
                'metric': metric,
                'original': original_perf,
                'migrated': migrated_perf,
                'regression': regression,
                'acceptable': abs(regression) <= 10  # 10% threshold
            })
        
        return results
```

## Output Format

1. **Migration Analysis**: Frontend codebase analysis (components, state, routing)
2. **Risk Assessment**: Identified risks with mitigation strategies
3. **Code Examples**: Automated component migration scripts and template converters
4. **Testing Strategy**: UI equivalence, user flow, and rendering tests
5. **Documentation**: Migration guide and runbooks

Focus on preserving user experience, component structure, and providing clear paths for successful frontend framework migration.

<!-- Related Templates -->
<!-- For backend migrations (languages, APIs, databases), see: backend/code-migrate.md -->
<!-- For migration planning, rollback strategies, and orchestration, see: general/code-migrate.md -->
