---
description: "Test CI/CD Integration"
model: claude-sonnet-4-0
complexity: intermediate
priority: high
tags: [testing, ci, cloud]
depends_on: []
chains_to: []
skip_if: [no_ci]
version: 1.0.0
---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Test CI/CD Integration

You are a CI/CD expert specializing in integrating comprehensive test suites into continuous integration and delivery pipelines. Design CI/CD workflows that run unit, integration, end-to-end, performance, security, mutation, and contract tests with proper caching, parallelization, and reporting.

## Context
The user needs CI/CD pipeline configuration for running their test suite. Focus on creating reliable, fast pipelines with proper service dependencies, caching, and test result reporting.

## Requirements
$ARGUMENTS

## Instructions

### CI/CD Integration

**GitHub Actions Workflow**
```yaml
# {{CLOUD_PATH_CI}}/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_ENV: test
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
        node-version: [16, 18, 20]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Set up Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
    
    - name: Cache Python dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Cache Node dependencies
      uses: actions/cache@v3
      with:
        path: ~/.npm
        key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
        restore-keys: |
          ${{ runner.os }}-node-
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Install Node dependencies
      run: npm ci
    
    - name: Lint Python code
      run: |
        flake8 src tests
        black --check src tests
        isort --check-only src tests
        mypy src
    
    - name: Lint JavaScript/TypeScript code
      run: |
        npm run lint
        npm run type-check
    
    - name: Run security scans
      run: |
        bandit -r src
        npm audit --audit-level high
        safety check
    
    - name: Run Python unit tests
      run: |
        pytest {{PATH_TESTS}}/unit/ -v --cov=src --cov-report=xml --junitxml=pytest-results.xml
    
    - name: Run JavaScript unit tests
      run: |
        npm run test:unit -- --coverage --ci --watchAll=false
    
    - name: Run integration tests
      run: |
        pytest {{PATH_TESTS}}/integration/ -v --junitxml=integration-results.xml
        npm run test:integration
    
    - name: Run end-to-end tests
      run: |
        pytest {{PATH_TESTS}}/e2e/ -v --junitxml=e2e-results.xml
        npm run test:e2e
    
    - name: Run performance tests
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        pytest {{PATH_TESTS}}/performance/ -v --junitxml=performance-results.xml
        npm run test:performance
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml,./coverage/lcov.info
        fail_ci_if_error: true
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results-${{ matrix.python-version }}-${{ matrix.node-version }}
        path: |
          *-results.xml
          coverage/
          htmlcov/
    
    - name: Comment PR with test results
      if: github.event_name == 'pull_request'
      uses: dorny/test-reporter@v1
      with:
        name: Test Results
        path: '*-results.xml'
        reporter: java-junit

  mutation-testing:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install mutmut
    
    - name: Run mutation testing
      run: |
        mutmut run --paths-to-mutate {{PATH_SRC}}/
        mutmut results
        mutmut html
    
    - name: Upload mutation test results
      uses: actions/upload-artifact@v3
      with:
        name: mutation-test-results
        path: html/

  contract-testing:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install pact-python
    
    - name: Run Pact consumer tests
      run: |
        pytest {{PATH_TESTS}}/contract/ -v
    
    - name: Publish Pacts
      if: github.ref == 'refs/heads/main'
      run: |
        pact-broker publish pacts/ --broker-base-url ${{ secrets.PACT_BROKER_URL }} --broker-token ${{ secrets.PACT_BROKER_TOKEN }}
```

## Related Templates

<!-- For backend (Python/Go/Java) testing, see: backend/test-harness.md -->
<!-- For frontend (JavaScript/TypeScript) testing, see: frontend/test-harness.md -->
<!-- For test data management and cross-command orchestration, see: general/test-harness.md -->
