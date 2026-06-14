---
model: claude-sonnet-4-0
description: "Backend Code Migration - Languages, APIs, Databases"
complexity: advanced
priority: medium
tags: [migration, backend, database, api]
depends_on: [general/research_codebase]
chains_to: []
skip_if: []
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Backend Code Migration

You are a backend code migration expert specializing in language upgrades, API paradigm shifts, and database migrations. Generate comprehensive migration scripts, transformation tools, and ensure smooth backend transitions with minimal disruption.

## Context
The user needs to migrate backend code -- language versions, API paradigms, or database systems. Focus on maintaining data integrity, API contracts, and providing clear migration paths with rollback strategies.

## Requirements
$ARGUMENTS

## Instructions

### Migration Assessment (Overview)

Before migrating, analyze the backend codebase for language dependencies, API surface area, and database schemas. Use the full assessment tooling from [`general/code-migrate.md`](../general/code-migrate.md) for a comprehensive analysis including complexity scoring, risk identification, and effort estimation.

### 4. Language Migrations

Handle language version upgrades:

**Python 2 to 3 Migration**
```python
class Python2to3Migrator:
    def __init__(self):
        self.transformations = {
            'print_statement': self.transform_print,
            'unicode_literals': self.transform_unicode,
            'division': self.transform_division,
            'imports': self.transform_imports,
            'iterators': self.transform_iterators,
            'exceptions': self.transform_exceptions
        }
    
    def migrate_file(self, file_path):
        """Migrate single Python file from 2 to 3"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Try with 2to3 lib for syntax conversion first
            content = self._basic_syntax_conversion(content)
            tree = ast.parse(content)
        
        # Apply transformations
        transformer = Python3Transformer()
        new_tree = transformer.visit(tree)
        
        # Generate new code
        return astor.to_source(new_tree)
    
    def transform_print(self, content):
        """Transform print statements to functions"""
        # Simple regex for basic cases
        content = re.sub(
            r'print\s+([^(].*?)$',
            r'print(\1)',
            content,
            flags=re.MULTILINE
        )
        
        # Handle print with >>
        content = re.sub(
            r'print\s*>>\s*(\w+),\s*(.+?)$',
            r'print(\2, file=\1)',
            content,
            flags=re.MULTILINE
        )
        
        return content
    
    def transform_unicode(self, content):
        """Handle unicode literals"""
        # Remove u prefix from strings
        content = re.sub(r'u"([^"]*)"', r'"\1"', content)
        content = re.sub(r"u'([^']*)'", r"'\1'", content)
        
        # Convert unicode() to str()
        content = re.sub(r'\bunicode\(', 'str(', content)
        
        return content
    
    def transform_iterators(self, content):
        """Transform iterator methods"""
        replacements = {
            '.iteritems()': '.items()',
            '.iterkeys()': '.keys()',
            '.itervalues()': '.values()',
            'xrange': 'range',
            '.has_key(': ' in '
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content

class Python3Transformer(ast.NodeTransformer):
    """AST transformer for Python 3 migration"""
    
    def visit_Raise(self, node):
        """Transform raise statements"""
        if node.exc and node.cause:
            # raise Exception, args -> raise Exception(args)
            if isinstance(node.cause, ast.Str):
                node.exc = ast.Call(
                    func=node.exc,
                    args=[node.cause],
                    keywords=[]
                )
                node.cause = None
        
        return node
    
    def visit_ExceptHandler(self, node):
        """Transform except clauses"""
        if node.type and node.name:
            # except Exception, e -> except Exception as e
            if isinstance(node.name, ast.Name):
                node.name = node.name.id
        
        return node
```

### 5. API Migration

Migrate between API paradigms:

**REST to GraphQL Migration**
```javascript
class RESTToGraphQLMigrator {
    constructor(restEndpoints) {
        this.endpoints = restEndpoints;
        this.schema = {
            types: {},
            queries: {},
            mutations: {}
        };
    }
    
    generateGraphQLSchema() {
        // Analyze REST endpoints
        this.analyzeEndpoints();
        
        // Generate type definitions
        const typeDefs = this.generateTypeDefs();
        
        // Generate resolvers
        const resolvers = this.generateResolvers();
        
        return { typeDefs, resolvers };
    }
    
    analyzeEndpoints() {
        for (const endpoint of this.endpoints) {
            const { method, path, response, params } = endpoint;
            
            // Extract resource type
            const resourceType = this.extractResourceType(path);
            
            // Build GraphQL type
            if (!this.schema.types[resourceType]) {
                this.schema.types[resourceType] = this.buildType(response);
            }
            
            // Map to GraphQL operations
            if (method === 'GET') {
                this.addQuery(resourceType, path, params);
            } else if (['POST', 'PUT', 'PATCH'].includes(method)) {
                this.addMutation(resourceType, path, params, method);
            }
        }
    }
    
    generateTypeDefs() {
        let schema = 'type Query {\n';
        
        // Add queries
        for (const [name, query] of Object.entries(this.schema.queries)) {
            schema += `  ${name}${this.generateArgs(query.args)}: ${query.returnType}\n`;
        }
        
        schema += '}\n\ntype Mutation {\n';
        
        // Add mutations
        for (const [name, mutation] of Object.entries(this.schema.mutations)) {
            schema += `  ${name}${this.generateArgs(mutation.args)}: ${mutation.returnType}\n`;
        }
        
        schema += '}\n\n';
        
        // Add types
        for (const [typeName, fields] of Object.entries(this.schema.types)) {
            schema += `type ${typeName} {\n`;
            for (const [fieldName, fieldType] of Object.entries(fields)) {
                schema += `  ${fieldName}: ${fieldType}\n`;
            }
            schema += '}\n\n';
        }
        
        return schema;
    }
    
    generateResolvers() {
        const resolvers = {
            Query: {},
            Mutation: {}
        };
        
        // Generate query resolvers
        for (const [name, query] of Object.entries(this.schema.queries)) {
            resolvers.Query[name] = async (parent, args, context) => {
                // Transform GraphQL args to REST params
                const restParams = this.transformArgs(args, query.paramMapping);
                
                // Call REST endpoint
                const response = await fetch(
                    this.buildUrl(query.endpoint, restParams),
                    { method: 'GET' }
                );
                
                return response.json();
            };
        }
        
        // Generate mutation resolvers
        for (const [name, mutation] of Object.entries(this.schema.mutations)) {
            resolvers.Mutation[name] = async (parent, args, context) => {
                const { input } = args;
                
                const response = await fetch(
                    mutation.endpoint,
                    {
                        method: mutation.method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input)
                    }
                );
                
                return response.json();
            };
        }
        
        return resolvers;
    }
}
```

### 6. Database Migration

Migrate between database systems:

**SQL to NoSQL Migration**
```python
class SQLToNoSQLMigrator:
    def __init__(self, source_db, target_db):
        self.source = source_db
        self.target = target_db
        self.schema_mapping = {}
    
    def analyze_schema(self):
        """Analyze SQL schema for NoSQL conversion"""
        tables = self.get_sql_tables()
        
        for table in tables:
            # Get table structure
            columns = self.get_table_columns(table)
            relationships = self.get_table_relationships(table)
            
            # Design document structure
            doc_structure = self.design_document_structure(
                table, columns, relationships
            )
            
            self.schema_mapping[table] = doc_structure
        
        return self.schema_mapping
    
    def design_document_structure(self, table, columns, relationships):
        """Design NoSQL document structure from SQL table"""
        structure = {
            'collection': self.to_collection_name(table),
            'fields': {},
            'embedded': [],
            'references': []
        }
        
        # Map columns to fields
        for col in columns:
            structure['fields'][col['name']] = {
                'type': self.map_sql_type_to_nosql(col['type']),
                'required': not col['nullable'],
                'indexed': col.get('is_indexed', False)
            }
        
        # Handle relationships
        for rel in relationships:
            if rel['type'] == 'one-to-one' or self.should_embed(rel):
                structure['embedded'].append({
                    'field': rel['field'],
                    'collection': rel['related_table']
                })
            else:
                structure['references'].append({
                    'field': rel['field'],
                    'collection': rel['related_table'],
                    'type': rel['type']
                })
        
        return structure
    
    def generate_migration_script(self):
        """Generate migration script"""
        script = """
import asyncio
from datetime import datetime

class DatabaseMigrator:
    def __init__(self, sql_conn, nosql_conn):
        self.sql = sql_conn
        self.nosql = nosql_conn
        self.batch_size = 1000
        
    async def migrate(self):
        start_time = datetime.now()
        
        # Create indexes
        await self.create_indexes()
        
        # Migrate data
        for table, mapping in schema_mapping.items():
            await self.migrate_table(table, mapping)
        
        # Verify migration
        await self.verify_migration()
        
        elapsed = datetime.now() - start_time
        print(f"Migration completed in {elapsed}")
    
    async def migrate_table(self, table, mapping):
        print(f"Migrating {table}...")
        
        total_rows = await self.get_row_count(table)
        migrated = 0
        
        async for batch in self.read_in_batches(table):
            documents = []
            
            for row in batch:
                doc = self.transform_row_to_document(row, mapping)
                
                # Handle embedded documents
                for embed in mapping['embedded']:
                    related_data = await self.fetch_related(
                        row, embed['field'], embed['collection']
                    )
                    doc[embed['field']] = related_data
                
                documents.append(doc)
            
            # Bulk insert
            await self.nosql[mapping['collection']].insert_many(documents)
            
            migrated += len(batch)
            progress = (migrated / total_rows) * 100
            print(f"  Progress: {progress:.1f}% ({migrated}/{total_rows})")
    
    def transform_row_to_document(self, row, mapping):
        doc = {}
        
        for field, config in mapping['fields'].items():
            value = row.get(field)
            
            # Type conversion
            if value is not None:
                doc[field] = self.convert_value(value, config['type'])
            elif config['required']:
                doc[field] = self.get_default_value(config['type'])
        
        # Add metadata
        doc['_migrated_at'] = datetime.now()
        doc['_source_table'] = mapping['collection']
        
        return doc
"""
        return script
```

### 7. Backend Testing Strategy

Ensure backend migration correctness with data integrity, API contract, and performance testing:

```python
class BackendMigrationTester:
    def __init__(self, original_app, migrated_app):
        self.original = original_app
        self.migrated = migrated_app
        self.test_results = []
    
    def run_comparison_tests(self):
        """Run side-by-side comparison tests for backend systems"""
        test_suites = [
            self.test_data_integrity,
            self.test_api_compatibility,
            self.test_performance
        ]
        
        for suite in test_suites:
            results = suite()
            self.test_results.extend(results)
        
        return self.generate_report()
    
    def test_data_integrity(self):
        """Verify data was migrated correctly"""
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
    
    def test_api_compatibility(self):
        """Verify API contracts are preserved after migration"""
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
        """Compare performance metrics for backend services"""
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

1. **Migration Analysis**: Backend codebase analysis (language, API, database)
2. **Risk Assessment**: Identified risks with mitigation strategies
3. **Code Examples**: Automated migration scripts and transformations
4. **Testing Strategy**: Data integrity, API contract, and performance tests
5. **Documentation**: Migration guide and runbooks

Focus on maintaining data integrity, preserving API contracts, and providing clear paths for successful backend migration.

<!-- Related Templates -->
<!-- For frontend framework migrations (React, Vue, etc.), see: frontend/code-migrate.md -->
<!-- For migration planning, rollback strategies, and orchestration, see: general/code-migrate.md -->
