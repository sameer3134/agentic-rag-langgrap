---
description: "Test Data Management & Orchestration"
model: claude-sonnet-4-0
---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Test Data Management & Orchestration

This is the shared orchestration template for the test harness. It covers test data factories, cross-command integration patterns, and end-to-end workflow validation that span backend, frontend, and cloud concerns. For domain-specific test implementations, see the related templates listed at the bottom.

## Requirements
$ARGUMENTS

## Instructions

### Test Data Management

**Test Data Factories**
```python
# {{PATH_TESTS}}/fixtures/data_factories.py
import factory
from datetime import datetime, timedelta
from faker import Faker
import random

fake = Faker()

class UserFactory(factory.Factory):
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda obj: fake.email())
    username = factory.LazyAttribute(lambda obj: fake.user_name())
    full_name = factory.LazyAttribute(lambda obj: fake.name())
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if extracted:
            obj['password'] = extracted
        else:
            obj['password'] = fake.password(length=12)

class AdminUserFactory(UserFactory):
    is_admin = True
    email = factory.LazyAttribute(lambda obj: f"admin_{fake.user_name()}@example.com")

class InactiveUserFactory(UserFactory):
    is_active = False

class RecentUserFactory(UserFactory):
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(1, 7))
    )

# Test data generators
class TestDataGenerator:
    @staticmethod
    def generate_test_users(count=10, user_type='standard'):
        """Generate test users of different types"""
        factories = {
            'standard': UserFactory,
            'admin': AdminUserFactory,
            'inactive': InactiveUserFactory,
            'recent': RecentUserFactory
        }
        
        factory_class = factories.get(user_type, UserFactory)
        return factory_class.build_batch(count)
    
    @staticmethod
    def generate_large_dataset(users=1000, posts=5000, comments=10000):
        """Generate large test dataset for performance testing"""
        return {
            'users': UserFactory.build_batch(users),
            'posts': PostFactory.build_batch(posts),
            'comments': CommentFactory.build_batch(comments)
        }
```

## Cross-Command Integration

### Complete Development Workflow Integration

**API Development + Testing Pipeline**
```bash
# 1. Generate API scaffolding
/api-scaffold
project_type: "microservice"
framework: "fastapi"
features: ["auth", "database", "monitoring"]

# 2. Generate comprehensive test suite
/test-harness
test_types: ["unit", "integration", "e2e", "performance", "security"]
framework: "pytest"
coverage_threshold: 90

# 3. Run security scans on tests
/security-scan
include_test_code: true
scan_types: ["static", "dependency", "secrets"]

# 4. Optimize Docker for testing
/docker-optimize
environment: "test"
include_test_data: true
optimization_level: "speed"
```

**Test-Driven Development Workflow**
```python
# Generated test configuration that integrates with all tools
class IntegratedTestConfig:
    def __init__(self):
        self.api_config = self.load_api_config()  # From /api-scaffold
        self.security_config = self.load_security_config()  # From /security-scan
        self.db_config = self.load_db_config()  # From /db-migrate
        
    def create_test_suite(self):
        """Create integrated test suite for all generated components"""
        return {
            'api_tests': self.generate_api_tests(),
            'security_tests': self.generate_security_tests(),
            'db_tests': self.generate_db_tests(),
            'integration_tests': self.generate_integration_tests()
        }
    
    def generate_api_tests(self):
        """Generate tests for API scaffold output"""
        endpoints = self.api_config.get('endpoints', [])
        return [
            self.create_endpoint_test(endpoint) 
            for endpoint in endpoints
        ]
    
    def generate_security_tests(self):
        """Generate tests based on security scan configuration"""
        return {
            'auth_tests': self.create_auth_tests(),
            'input_validation_tests': self.create_validation_tests(),
            'rate_limiting_tests': self.create_rate_limit_tests()
        }
```

**Database + Testing Integration**
```python
# conftest.py - Database test configuration
import pytest
from src.database import get_db_connection

@pytest.fixture(scope="session")
def db_migration_config():
    """Load database configuration from /db-migrate"""
    return {
        'source_db': 'postgresql://test:test@localhost:5432/source_test',
        'target_db': 'postgresql://test:test@localhost:5432/target_test',
        'migration_scripts': './{{BE_PATH_MIGRATIONS}}/test/',
        'test_data': './fixtures/test_data.sql'
    }

@pytest.fixture
def test_database(db_migration_config):
    """Setup test database with migrations"""
    # Apply migrations from /db-migrate output
    apply_test_migrations(db_migration_config['migration_scripts'])
    
    # Load test data
    load_test_fixtures(db_migration_config['test_data'])
    
    yield get_db_connection(db_migration_config['target_db'])
    
    # Cleanup
    teardown_test_database()
```

**Frontend + Backend Integration Testing**
```javascript
// Integration test configuration
// {{PATH_TESTS}}/integration/fullstack.test.js
import { setupTestEnvironment } from './utils/testSetup';

describe('Full Stack Integration', () => {
  beforeAll(async () => {
    // Start backend from /api-scaffold
    await startTestBackend({
      config: require('../../backend/test.config.json')
    });
    
    // Start frontend from /frontend-optimize
    await startTestFrontend({
      mode: 'test',
      apiUrl: 'http://localhost:8000/api/v1'
    });
  });
  
  test('complete user journey', async () => {
    // Test generated by combining frontend and backend tests
    const userFlow = await setupUserFlow();
    
    // API tests from backend
    const apiResponse = await userFlow.createUser(testUserData);
    expect(apiResponse.status).toBe(201);
    
    // Frontend tests
    await userFlow.navigateToLogin();
    await userFlow.login(testUserData.email, testUserData.password);
    await userFlow.verifyDashboard();
  });
});
```

**{{CLOUD_ORCHESTRATOR}} + Testing Integration**
```yaml
# Generated {{CLOUD_ORCHESTRATOR}} test configuration
# k8s-test-environment.yaml (integrates with /k8s-manifest output)
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
data:
  test-database-url: "postgresql://test:test@postgres-test:5432/testdb"
  test-redis-url: "redis://redis-test:6379/0"
  test-api-url: "http://api-test:8000"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-runner
spec:
  template:
    spec:
      containers:
      - name: test-runner
        image: test-runner:latest
        env:
        - name: TEST_ENVIRONMENT
          value: "k8s"
        - name: API_URL
          valueFrom:
            configMapKeyRef:
              name: test-config
              key: test-api-url
        command: ["pytest", "{{PATH_TESTS}}/", "-v", "--k8s-integration"]
```

**CI/CD Integration Example**
```yaml
# {{CLOUD_PATH_CI}}/integrated-testing.yml
name: Integrated Testing Pipeline

on:
  pull_request:
    branches: [main]

jobs:
  setup-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    # 1. Build application using /docker-optimize
    - name: Build optimized containers
      run: |
        docker build -f Dockerfile.optimized -t app:test .
        docker build -f Dockerfile.test -t test-runner:latest .
    
    # 2. Setup infrastructure using /k8s-manifest
    - name: Setup test cluster
      run: |
        kind create cluster --config k8s-test-cluster.yaml
        kubectl apply -f k8s-test-manifests/
    
    # 3. Run database migrations using /db-migrate
    - name: Run test migrations
      run: |
        kubectl run migration-job --image=migrator:latest \
          --env="DATABASE_URL=${{ secrets.TEST_DB_URL }}"
    
    # 4. Execute comprehensive test suite
    - name: Run test harness
      run: |
        kubectl run test-job --image=test-runner:latest \
          --env="TEST_SUITE=full" \
          --env="COVERAGE_THRESHOLD=90"
    
    # 5. Security scanning of test results
    - name: Security scan test artifacts
      run: |
        /security-scan test-results/ --format junit
    
    # 6. Performance baseline validation
    - name: Performance regression testing
      run: |
        kubectl run performance-test --image=test-runner:latest \
          --env="TEST_SUITE=performance" \
          --env="BASELINE_FILE=performance-baseline.json"
```

**Configuration Sharing Between Commands**
```json
// shared-config.json - Used across all commands
{
  "project": {
    "name": "microservice-api",
    "type": "backend",
    "framework": "fastapi",
    "database": "postgresql",
    "cache": "redis"
  },
  "testing": {
    "framework": "pytest",
    "coverage_threshold": 90,
    "test_types": ["unit", "integration", "e2e", "performance", "security"],
    "parallel_execution": true,
    "test_data_strategy": "factories"
  },
  "security": {
    "auth_method": "jwt",
    "password_hashing": "bcrypt",
    "rate_limiting": true,
    "input_validation": "pydantic"
  },
  "deployment": {
    "platform": "kubernetes",
    "environment": "production",
    "scaling": "horizontal",
    "monitoring": "prometheus"
  }
}
```

**Shared Test Utilities**
```python
# {{PATH_TESTS}}/utils/integration_helpers.py
class CrossCommandTestHelper:
    """Helper for running tests across command outputs"""
    
    def __init__(self, config_path="shared-config.json"):
        self.config = self.load_shared_config(config_path)
        self.api_client = self.setup_api_client()
        self.db_client = self.setup_db_client()
        
    def test_api_database_integration(self):
        """Test API + Database integration"""
        # Create test data via API (from /api-scaffold)
        user_data = self.create_test_user_via_api()
        
        # Verify in database (using /db-migrate schema)
        db_user = self.get_user_from_db(user_data['id'])
        assert db_user is not None
        
        # Test API retrieval
        api_user = self.get_user_via_api(user_data['id'])
        assert api_user['email'] == db_user.email
    
    def test_security_compliance(self):
        """Test security compliance across all components"""
        # Run security tests from /security-scan config
        security_results = self.run_security_tests()
        
        # Validate API security
        auth_tests = self.run_auth_tests()
        
        # Validate database security
        db_security = self.check_database_security()
        
        return {
            'security_scan': security_results,
            'auth_tests': auth_tests,
            'database_security': db_security
        }
    
    def test_performance_benchmarks(self):
        """Test performance across all components"""
        return {
            'api_performance': self.benchmark_api_endpoints(),
            'database_performance': self.benchmark_db_queries(),
            'integration_performance': self.benchmark_full_workflow()
        }
```

**End-to-End Workflow Example**
```python
# Complete workflow test
@pytest.mark.integration
@pytest.mark.slow
def test_complete_development_workflow():
    """Test the complete output from all slash commands working together"""
    
    # 1. API + Database Integration
    api_client = get_api_client()  # From /api-scaffold
    db_client = get_db_client()    # From /db-migrate
    
    # Create user via API
    user_response = api_client.post('/users/', json=test_user_data)
    assert user_response.status_code == 201
    
    # Verify in database
    user_id = user_response.json()['id']
    db_user = db_client.get_user(user_id)
    assert db_user is not None
    
    # 2. Security Validation
    # Test JWT token from API
    token = authenticate_user(test_user_data['email'], test_user_data['password'])
    assert validate_jwt_token(token)
    
    # Test rate limiting (from /security-scan)
    assert test_rate_limiting(api_client)
    
    # 3. Performance Validation
    # Test API performance
    api_metrics = benchmark_api_endpoint('/users/', method='POST')
    assert api_metrics['avg_response_time'] < 200  # ms
    
    # 4. Container Integration
    # Test Docker container from /docker-optimize
    container_health = check_container_health('app:latest')
    assert container_health['status'] == 'healthy'
    
    # 5. {{CLOUD_ORCHESTRATOR}} Integration
    # Test {{CLOUD_ORCHESTRATOR}} deployment from /k8s-manifest
    k8s_status = check_k8s_deployment_status('api-deployment')
    assert k8s_status['ready_replicas'] > 0
```

This integration approach ensures all generated code works together seamlessly and provides comprehensive validation across the entire application stack.

## Validation Checklist

- [ ] Testing framework selected based on technology stack
- [ ] Unit tests cover core business logic
- [ ] Integration tests validate component interactions
- [ ] End-to-end tests verify user workflows
- [ ] Performance tests establish baselines
- [ ] Security tests validate security controls
- [ ] Property-based tests explore edge cases
- [ ] Contract tests ensure API compatibility
- [ ] Mutation tests validate test quality
- [ ] CI/CD pipeline includes all test types
- [ ] Test coverage meets minimum thresholds
- [ ] Test data management strategy implemented
- [ ] Test environment properly configured

Focus on creating a comprehensive testing strategy that ensures code quality, performance, and security while maintaining fast feedback loops and reliable test execution.

## Related Templates

- **backend/test-harness.md** - Python/Go/Java testing: unit, integration, e2e, performance, security, and contract tests
- **frontend/test-harness.md** - JavaScript/TypeScript testing: Jest, Playwright, property-based testing with fast-check
- **cloud/test-harness.md** - CI/CD pipeline configuration: GitHub Actions workflows, mutation testing, contract test publishing
