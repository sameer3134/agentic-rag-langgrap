---
description: "Backend Testing Framework - Python/Go/Java"
model: claude-sonnet-4-0
complexity: advanced
priority: critical
tags: [testing, backend, ci]
depends_on: []
chains_to: [review/validate_plan]
skip_if: []
version: 1.0.0
---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Backend Test Harness Generator

You are a testing expert specializing in creating comprehensive, maintainable, and efficient test suites for backend applications. Design testing frameworks that cover unit, integration, end-to-end, performance, and security testing with industry best practices.

## Context
The user needs a complete backend testing strategy and implementation. Focus on creating a robust testing pyramid with appropriate tools, patterns, and automation that ensures code quality and reliability.

## Requirements
$ARGUMENTS

## Instructions

### 1. Testing Framework Selection (Backend)

Choose appropriate testing frameworks based on backend technology stack:

**Framework Selection Matrix**
```python
def select_testing_framework(tech_stack, project_type):
    """Select optimal testing frameworks based on backend technology"""
    
    frameworks = {
        'python': {
            'unit_testing': 'pytest',
            'mocking': 'pytest-mock, unittest.mock',
            'property_testing': 'hypothesis',
            'load_testing': 'locust',
            'contract_testing': 'pact-python',
            'security_testing': 'bandit, safety',
            'api_testing': 'requests, httpx',
            'async_testing': 'pytest-asyncio'
        },
        'java': {
            'unit_testing': 'junit5, testng',
            'mocking': 'mockito, powermock',
            'property_testing': 'jqwik',
            'load_testing': 'gatling, jmeter',
            'contract_testing': 'pact-jvm',
            'security_testing': 'spotbugs, dependency-check',
            'api_testing': 'rest-assured',
            'integration_testing': 'testcontainers'
        },
        'go': {
            'unit_testing': 'testing, testify',
            'mocking': 'testify/mock, gomock',
            'property_testing': 'gopter',
            'load_testing': 'vegeta, hey',
            'contract_testing': 'pact-go',
            'security_testing': 'gosec, nancy',
            'api_testing': 'ginkgo, httptest',
            'fuzzing': 'go-fuzz'
        }
    }
    
    return frameworks.get(tech_stack, frameworks['python'])
```

### 2. Python Testing Implementation

Complete Python testing framework with pytest:

**Project Structure**
```
project/
├── {{PATH_SRC}}/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── payment_service.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
├── {{PATH_TESTS}}/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_utils.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_external_services.py
│   ├── e2e/
│   │   ├── test_user_flows.py
│   │   └── test_payment_flows.py
│   ├── performance/
│   │   ├── test_load.py
│   │   └── test_stress.py
│   ├── security/
│   │   ├── test_auth.py
│   │   └── test_input_validation.py
│   └── fixtures/
│       ├── __init__.py
│       ├── data_factories.py
│       └── test_data.py
├── pytest.ini
├── requirements-test.txt
└── {{CLOUD_PATH_CI}}/test.yml
```

**Test Configuration**
```ini
# pytest.ini
[tool:pytest]
minversion = 7.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=90
    --junitxml=pytest-results.xml
    --tb=short
    -p no:warnings
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    security: Security tests
    performance: Performance tests
    smoke: Smoke tests
    regression: Regression tests
    api: API tests
    database: Database tests
    external: Tests requiring external services
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning
```

**Advanced Test Configuration**
```python
# conftest.py
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis
from datetime import datetime, timedelta
import factory
from faker import Faker

from src.database import Base
from src.main import app
from src.config import Settings

fake = Faker()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line(
        "markers", "vcr: mark test to use VCR cassettes"
    )
    config.addinivalue_line(
        "markers", "freeze_time: mark test to freeze time"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database fixtures
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(test_db_engine):
    """Create database session for test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# API client fixtures
@pytest.fixture
def api_client():
    """Create test API client"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create authenticated API client"""
    # Login and get token
    login_data = {"email": test_user.email, "password": "testpass123"}
    response = api_client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    # Set authorization header
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    yield api_client

# Data factories
class UserFactory(factory.Factory):
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda obj: fake.email())
    username = factory.LazyAttribute(lambda obj: fake.user_name())
    full_name = factory.LazyAttribute(lambda obj: fake.name())
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)

@pytest.fixture
def test_user():
    """Create test user"""
    return UserFactory()

@pytest.fixture
def test_users():
    """Create multiple test users"""
    return UserFactory.build_batch(5)

# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = Mock(spec=redis.Redis)
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = 0
    return redis_mock

@pytest.fixture
def mock_email_service():
    """Mock email service"""
    mock = AsyncMock()
    mock.send_email.return_value = {"status": "sent", "message_id": "test-123"}
    return mock

@pytest.fixture
def mock_payment_gateway():
    """Mock payment gateway"""
    mock = Mock()
    mock.process_payment.return_value = {
        "transaction_id": "txn_123",
        "status": "success",
        "amount": 100.00
    }
    return mock

# Time fixtures
@pytest.fixture
def freeze_time():
    """Freeze time for testing"""
    from freezegun import freeze_time as _freeze_time
    with _freeze_time("2024-01-01 12:00:00") as frozen_time:
        yield frozen_time

# File system fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

# Environment fixtures
@pytest.fixture
def test_settings():
    """Test application settings"""
    return Settings(
        TESTING=True,
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-key"
    )

# Network fixtures
@pytest.fixture(scope="session")
def vcr_config():
    """VCR configuration for recording HTTP interactions"""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "match_on": ["uri", "method"],
        "cassette_library_dir": "{{PATH_TESTS}}/fixtures/cassettes"
    }
```

**Unit Testing Implementation**
```python
# {{PATH_TESTS}}/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from hypothesis import given, strategies as st

from src.services.user_service import UserService
from src.models.user import User
from src.exceptions import UserNotFoundError, DuplicateEmailError

class TestUserService:
    """Test suite for UserService"""
    
    @pytest.fixture
    def user_service(self, db_session):
        """Create UserService instance"""
        return UserService(db_session)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "securepass123"
        }
    
    def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation"""
        # Act
        user = user_service.create_user(sample_user_data)
        
        # Assert
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.is_active is True
        assert user.created_at is not None
        assert hasattr(user, 'hashed_password') is False  # Password not exposed
    
    def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test user creation with duplicate email"""
        # Arrange
        user_service.create_user(sample_user_data)
        
        # Act & Assert
        with pytest.raises(DuplicateEmailError) as exc_info:
            user_service.create_user(sample_user_data)
        
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "@example.com",
        "test@",
        "",
        None
    ])
    def test_create_user_invalid_email(self, user_service, sample_user_data, invalid_email):
        """Test user creation with invalid email formats"""
        # Arrange
        sample_user_data["email"] = invalid_email
        
        # Act & Assert
        with pytest.raises(ValueError):
            user_service.create_user(sample_user_data)
    
    @given(
        email=st.emails(),
        username=st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=['L', 'N'])),
        full_name=st.text(min_size=1, max_size=100)
    )
    def test_create_user_property_based(self, user_service, email, username, full_name):
        """Property-based test for user creation"""
        # Arrange
        user_data = {
            "email": email,
            "username": username,
            "full_name": full_name,
            "password": "validpassword123"
        }
        
        # Act
        user = user_service.create_user(user_data)
        
        # Assert
        assert user.email == email
        assert user.username == username
        assert user.full_name == full_name
    
    def test_get_user_by_id_success(self, user_service, test_user):
        """Test retrieving user by ID"""
        # Arrange
        created_user = user_service.create_user(test_user)
        
        # Act
        retrieved_user = user_service.get_user_by_id(created_user.id)
        
        # Assert
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    def test_get_user_by_id_not_found(self, user_service):
        """Test retrieving non-existent user"""
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            user_service.get_user_by_id(99999)
    
    @patch('src.services.user_service.send_welcome_email')
    def test_create_user_sends_welcome_email(self, mock_send_email, user_service, sample_user_data):
        """Test that welcome email is sent on user creation"""
        # Act
        user = user_service.create_user(sample_user_data)
        
        # Assert
        mock_send_email.assert_called_once_with(user.email, user.full_name)
    
    @pytest.mark.asyncio
    async def test_create_user_async(self, user_service, sample_user_data):
        """Test async user creation"""
        # Act
        user = await user_service.create_user_async(sample_user_data)
        
        # Assert
        assert user.email == sample_user_data["email"]
    
    def test_update_user_success(self, user_service, test_user):
        """Test successful user update"""
        # Arrange
        created_user = user_service.create_user(test_user)
        update_data = {"full_name": "Updated Name"}
        
        # Act
        updated_user = user_service.update_user(created_user.id, update_data)
        
        # Assert
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == created_user.email  # Unchanged
    
    def test_authenticate_user_success(self, user_service, sample_user_data):
        """Test successful user authentication"""
        # Arrange
        user = user_service.create_user(sample_user_data)
        
        # Act
        authenticated_user = user_service.authenticate_user(
            sample_user_data["email"], 
            sample_user_data["password"]
        )
        
        # Assert
        assert authenticated_user.id == user.id
    
    def test_authenticate_user_wrong_password(self, user_service, sample_user_data):
        """Test authentication with wrong password"""
        # Arrange
        user_service.create_user(sample_user_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            user_service.authenticate_user(
                sample_user_data["email"], 
                "wrongpassword"
            )
```

**Integration Testing Implementation**
```python
# {{PATH_TESTS}}/integration/test_api_endpoints.py
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

class TestUserAPIEndpoints:
    """Integration tests for User API endpoints"""
    
    def test_create_user_endpoint(self, api_client):
        """Test user creation endpoint"""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "full_name": "New User"
        }
        
        # Act
        response = api_client.post("/api/v1/users/", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "password" not in data
    
    def test_create_user_validation_error(self, api_client):
        """Test user creation with validation errors"""
        # Arrange
        invalid_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123"  # Too short
        }
        
        # Act
        response = api_client.post("/api/v1/users/", json=invalid_data)
        
        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in error["loc"] for error in errors)
        assert any("username" in error["loc"] for error in errors)
        assert any("password" in error["loc"] for error in errors)
    
    def test_get_user_authenticated(self, authenticated_client, test_user):
        """Test getting user profile when authenticated"""
        # Act
        response = authenticated_client.get("/api/v1/users/me")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
    
    def test_get_user_unauthenticated(self, api_client):
        """Test getting user profile without authentication"""
        # Act
        response = api_client.get("/api/v1/users/me")
        
        # Assert
        assert response.status_code == 401
    
    def test_rate_limiting(self, api_client):
        """Test API rate limiting"""
        # Arrange
        endpoint = "/api/v1/users/"
        user_data = {
            "email": f"test{i}@example.com",
            "username": f"user{i}",
            "password": "securepass123"
        }
        
        # Act - Make rapid requests
        responses = []
        for i in range(102):  # Exceed rate limit of 100
            user_data["email"] = f"test{i}@example.com"
            user_data["username"] = f"user{i}"
            response = api_client.post(endpoint, json=user_data)
            responses.append(response)
        
        # Assert
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests
    
    @pytest.mark.slow
    def test_bulk_user_operations(self, api_client):
        """Test creating and managing multiple users"""
        # Arrange
        user_count = 50
        users_data = [
            {
                "email": f"bulk{i}@example.com",
                "username": f"bulkuser{i}",
                "password": "securepass123",
                "full_name": f"Bulk User {i}"
            }
            for i in range(user_count)
        ]
        
        # Act - Create users
        created_users = []
        for user_data in users_data:
            response = api_client.post("/api/v1/users/", json=user_data)
            assert response.status_code == 201
            created_users.append(response.json())
        
        # Act - List users
        response = api_client.get("/api/v1/users/?limit=100")
        
        # Assert
        assert response.status_code == 200
        users_list = response.json()
        assert len(users_list) >= user_count
```

**End-to-End Testing Implementation**
```python
# {{PATH_TESTS}}/e2e/test_user_flows.py
import pytest
from playwright.async_api import async_playwright, Page
import asyncio

@pytest.mark.e2e
class TestUserFlows:
    """End-to-end tests for user workflows"""
    
    @pytest.fixture
    async def browser_page(self):
        """Create browser page for testing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            yield page
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_user_registration_flow(self, browser_page: Page):
        """Test complete user registration flow"""
        # Navigate to registration page
        await browser_page.goto("http://localhost:3000/register")
        
        # Fill registration form
        await browser_page.fill('[data-testid="email-input"]', 'e2e@example.com')
        await browser_page.fill('[data-testid="username-input"]', 'e2euser')
        await browser_page.fill('[data-testid="password-input"]', 'securepass123')
        await browser_page.fill('[data-testid="confirm-password-input"]', 'securepass123')
        
        # Submit form
        await browser_page.click('[data-testid="register-button"]')
        
        # Verify redirect to dashboard
        await browser_page.wait_for_url("**/dashboard")
        
        # Verify welcome message
        welcome_text = await browser_page.text_content('[data-testid="welcome-message"]')
        assert "Welcome, e2euser" in welcome_text
    
    @pytest.mark.asyncio
    async def test_login_logout_flow(self, browser_page: Page, test_user):
        """Test login and logout flow"""
        # Navigate to login page
        await browser_page.goto("http://localhost:3000/login")
        
        # Fill login form
        await browser_page.fill('[data-testid="email-input"]', test_user["email"])
        await browser_page.fill('[data-testid="password-input"]', test_user["password"])
        
        # Submit login
        await browser_page.click('[data-testid="login-button"]')
        
        # Verify successful login
        await browser_page.wait_for_url("**/dashboard")
        
        # Test logout
        await browser_page.click('[data-testid="user-menu"]')
        await browser_page.click('[data-testid="logout-button"]')
        
        # Verify redirect to home page
        await browser_page.wait_for_url("**/")
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, browser_page: Page):
        """Test password reset flow"""
        # Navigate to password reset page
        await browser_page.goto("http://localhost:3000/forgot-password")
        
        # Fill email
        await browser_page.fill('[data-testid="email-input"]', 'test@example.com')
        
        # Submit request
        await browser_page.click('[data-testid="reset-button"]')
        
        # Verify success message
        success_message = await browser_page.text_content('[data-testid="success-message"]')
        assert "reset link sent" in success_message.lower()
```

**Performance Testing Implementation**
```python
# {{PATH_TESTS}}/performance/test_load.py
import pytest
import asyncio
import aiohttp
import time
from statistics import mean, median
from concurrent.futures import ThreadPoolExecutor
import locust
from locust import HttpUser, task, between

class APILoadTest(HttpUser):
    """Locust load test for API endpoints"""
    
    wait_time = between(1, 3)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Setup for each user"""
        # Create test user and login
        user_data = {
            "email": f"loadtest{self.host}@example.com",
            "username": f"loaduser{int(time.time())}",
            "password": "loadtest123"
        }
        
        response = self.client.post("/api/v1/users/", json=user_data)
        if response.status_code == 201:
            # Login to get token
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            login_response = self.client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(3)
    def get_user_profile(self):
        """Test getting user profile"""
        self.client.get("/api/v1/users/me")
    
    @task(2)
    def list_users(self):
        """Test listing users"""
        self.client.get("/api/v1/users/?limit=10")
    
    @task(1)
    def update_profile(self):
        """Test updating user profile"""
        update_data = {"full_name": "Updated Name"}
        self.client.put("/api/v1/users/me", json=update_data)

@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self):
        """Test concurrent user creation performance"""
        async def create_user(session, user_id):
            user_data = {
                "email": f"perf{user_id}@example.com",
                "username": f"perfuser{user_id}",
                "password": "perftest123"
            }
            
            start_time = time.time()
            async with session.post(
                "http://localhost:8000/api/v1/users/",
                json=user_data
            ) as response:
                end_time = time.time()
                return {
                    "status": response.status,
                    "duration": end_time - start_time,
                    "user_id": user_id
                }
        
        # Test with 100 concurrent requests
        async with aiohttp.ClientSession() as session:
            tasks = [create_user(session, i) for i in range(100)]
            results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful_requests = [r for r in results if r["status"] == 201]
        durations = [r["duration"] for r in successful_requests]
        
        # Assertions
        assert len(successful_requests) >= 95  # 95% success rate
        assert mean(durations) < 1.0  # Average response time < 1s
        assert max(durations) < 5.0   # Max response time < 5s
        assert median(durations) < 0.5  # Median response time < 0.5s
    
    def test_database_query_performance(self, db_session):
        """Test database query performance"""
        # Create test data
        users = []
        for i in range(1000):
            user_data = {
                "email": f"dbperf{i}@example.com",
                "username": f"dbperfuser{i}",
                "password": "dbperftest123"
            }
            user = user_service.create_user(user_data)
            users.append(user)
        
        # Test query performance
        start_time = time.time()
        result = db_session.query(User).limit(100).all()
        query_time = time.time() - start_time
        
        # Assertions
        assert len(result) == 100
        assert query_time < 0.1  # Query should complete in < 100ms
    
    @pytest.mark.slow
    def test_memory_usage(self):
        """Test memory usage during operations"""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        users = []
        for i in range(10000):
            user_data = {
                "email": f"mem{i}@example.com",
                "username": f"memuser{i}",
                "password": "memtest123"
            }
            users.append(user_data)
        
        # Check memory after operations
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Cleanup
        del users
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Assertions
        assert memory_increase < 100  # Memory increase < 100MB
        assert final_memory - initial_memory < 10  # Memory leak < 10MB
```

**Security Testing Implementation**
```python
# {{PATH_TESTS}}/security/test_auth.py
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

@pytest.mark.security
class TestAuthenticationSecurity:
    """Security tests for authentication system"""
    
    def test_password_hashing(self, user_service):
        """Test password is properly hashed"""
        # Arrange
        user_data = {
            "email": "security@example.com",
            "username": "securityuser",
            "password": "plainpassword123"
        }
        
        # Act
        user = user_service.create_user(user_data)
        
        # Assert
        # Password should be hashed, not stored in plain text
        assert user.hashed_password != user_data["password"]
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long
        assert user.hashed_password.startswith("$2b$")  # Bcrypt format
    
    def test_jwt_token_expiration(self, api_client, test_user):
        """Test JWT token expiration"""
        # Arrange - Create user and login
        api_client.post("/api/v1/users/", json=test_user)
        login_response = api_client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]
        
        # Act - Decode token to check expiration
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        
        # Assert
        assert exp_datetime > datetime.utcnow()  # Token not expired
        assert exp_datetime < datetime.utcnow() + timedelta(days=8)  # Reasonable expiry
    
    def test_invalid_token_rejection(self, api_client):
        """Test API rejects invalid tokens"""
        # Arrange
        invalid_tokens = [
            "invalid.token.format",
            "Bearer invalid_token",
            "",
            "expired_token_here"
        ]
        
        for invalid_token in invalid_tokens:
            # Act
            headers = {"Authorization": f"Bearer {invalid_token}"}
            response = api_client.get("/api/v1/users/me", headers=headers)
            
            # Assert
            assert response.status_code == 401
    
    def test_sql_injection_prevention(self, api_client):
        """Test SQL injection prevention"""
        # Arrange - Malicious payloads
        sql_injection_payloads = [
            "test'; DROP TABLE users; --",
            "test' OR '1'='1",
            "test' UNION SELECT * FROM users --",
            "'; DELETE FROM users WHERE '1'='1'; --"
        ]
        
        for payload in sql_injection_payloads:
            # Act
            user_data = {
                "email": f"{payload}@example.com",
                "username": payload,
                "password": "testpass123"
            }
            response = api_client.post("/api/v1/users/", json=user_data)
            
            # Assert - Should handle gracefully, not execute SQL
            assert response.status_code in [400, 422]  # Validation error, not SQL error
    
    def test_xss_prevention(self, api_client):
        """Test XSS prevention in API responses"""
        # Arrange
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            # Act
            user_data = {
                "email": "xsstest@example.com",
                "username": "xssuser",
                "full_name": payload,
                "password": "testpass123"
            }
            response = api_client.post("/api/v1/users/", json=user_data)
            
            if response.status_code == 201:
                # Assert - Response should be properly escaped
                response_text = response.text
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text
    
    def test_rate_limiting_security(self, api_client):
        """Test rate limiting prevents brute force attacks"""
        # Arrange
        login_data = {
            "email": "victim@example.com",
            "password": "wrongpassword"
        }
        
        # Act - Attempt multiple failed logins
        failed_attempts = 0
        for i in range(20):
            response = api_client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 429:  # Rate limited
                break
            failed_attempts += 1
        
        # Assert - Should be rate limited before 20 attempts
        assert failed_attempts < 15  # Rate limiting kicks in
    
    def test_csrf_protection(self, api_client):
        """Test CSRF protection for state-changing operations"""
        # This test depends on your CSRF implementation
        # Example for cookie-based sessions
        pass
    
    @pytest.mark.parametrize("sensitive_header", [
        "X-API-Key",
        "Authorization",
        "X-Access-Token"
    ])
    def test_sensitive_headers_not_logged(self, api_client, sensitive_header):
        """Test sensitive headers are not logged"""
        with patch('src.middleware.logger.info') as mock_logger:
            # Act
            headers = {sensitive_header: "sensitive_value"}
            api_client.get("/api/v1/users/", headers=headers)
            
            # Assert
            logged_calls = [str(call) for call in mock_logger.call_args_list]
            for call in logged_calls:
                assert "sensitive_value" not in call
```

**Contract Testing Implementation**
```python
# {{PATH_TESTS}}/contract/test_api_contract.py
import pytest
from pact import Consumer, Provider, Like, EachLike, Term
import requests

# Consumer test (API client perspective)
@pytest.fixture
def pact():
    """Create Pact consumer"""
    pact = Consumer('UserServiceClient').has_pact_with(Provider('UserServiceAPI'))
    pact.start()
    yield pact
    pact.stop()

class TestUserServiceContract:
    """Contract tests for User Service API"""
    
    def test_get_user_success(self, pact):
        """Test contract for successful user retrieval"""
        # Arrange
        expected_response = {
            'id': Like(123),
            'email': Like('user@example.com'),
            'username': Like('testuser'),
            'full_name': Like('Test User'),
            'is_active': Like(True),
            'created_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '2024-01-01T12:00:00')
        }
        
        (pact
         .given('user with ID 123 exists')
         .upon_receiving('a request for user 123')
         .with_request('GET', '/api/v1/users/123')
         .will_respond_with(200, body=expected_response))
        
        # Act
        with pact:
            response = requests.get('http://localhost:1234/api/v1/users/123')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['id'] == 123
    
    def test_create_user_success(self, pact):
        """Test contract for successful user creation"""
        # Arrange
        user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'securepass123'
        }
        
        expected_response = {
            'id': Like(456),
            'email': Like('newuser@example.com'),
            'username': Like('newuser'),
            'is_active': Like(True)
        }
        
        (pact
         .given('no user exists with email newuser@example.com')
         .upon_receiving('a request to create a user')
         .with_request('POST', '/api/v1/users/', body=user_data)
         .will_respond_with(201, body=expected_response))
        
        # Act
        with pact:
            response = requests.post(
                'http://localhost:1234/api/v1/users/',
                json=user_data
            )
        
        # Assert
        assert response.status_code == 201
        assert response.json()['email'] == 'newuser@example.com'
```

## Related Templates

<!-- For frontend (JavaScript/TypeScript) testing, see: frontend/test-harness.md -->
<!-- For CI/CD test integration, see: cloud/test-harness.md -->
<!-- For test data management and cross-command orchestration, see: general/test-harness.md -->
