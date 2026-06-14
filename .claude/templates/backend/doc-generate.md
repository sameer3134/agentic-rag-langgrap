---
description: "Backend API Documentation Generation"
model: claude-sonnet-4-0
complexity: intermediate
priority: medium
tags: [docs, api, backend]
depends_on: [backend/api-scaffold]
chains_to: []
skip_if: []
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

<!-- Related doc-generate templates:
  - general/doc-generate.md  (Architecture, Code, User Docs, Quality Checks)
  - frontend/doc-generate.md (Interactive Documentation)
  - cloud/doc-generate.md    (Documentation CI/CD Pipeline)
-->

# Backend API Documentation Generation

You are a documentation expert specializing in creating comprehensive, maintainable API documentation from backend code. Generate API docs, SDK references, and endpoint specifications using AI-powered analysis and industry best practices.

## Context
The user needs automated API documentation generation that extracts information from backend code, creates clear endpoint references, and maintains consistency across documentation types. Focus on creating living documentation that stays synchronized with backend code.

## Requirements
$ARGUMENTS

## Instructions

### 1. Code Analysis for Documentation (Backend Focus)

Extract documentation elements from backend source code:

**API Documentation Extraction**
```python
import ast
import inspect
from typing import Dict, List, Any

class APIDocExtractor:
    def extract_endpoints(self, code_path):
        """
        Extract API endpoints and their documentation
        """
        endpoints = []
        
        # {{BE_FRAMEWORK}} example
        fastapi_decorators = ['@app.get', '@app.post', '@app.put', '@app.delete']
        
        with open(code_path, 'r') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for route decorators
                for decorator in node.decorator_list:
                    if self._is_route_decorator(decorator):
                        endpoint = {
                            'method': self._extract_method(decorator),
                            'path': self._extract_path(decorator),
                            'function': node.name,
                            'docstring': ast.get_docstring(node),
                            'parameters': self._extract_parameters(node),
                            'returns': self._extract_returns(node),
                            'examples': self._extract_examples(node)
                        }
                        endpoints.append(endpoint)
                        
        return endpoints
    
    def _extract_parameters(self, func_node):
        """
        Extract function parameters with types
        """
        params = []
        for arg in func_node.args.args:
            param = {
                'name': arg.arg,
                'type': None,
                'required': True,
                'description': ''
            }
            
            # Extract type annotation
            if arg.annotation:
                param['type'] = ast.unparse(arg.annotation)
                
            params.append(param)
            
        return params
```

**Type and Schema Documentation**
```python
# Extract Pydantic models
def extract_pydantic_schemas(file_path):
    """
    Extract Pydantic model definitions for API documentation
    """
    schemas = []
    
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
        
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if inherits from BaseModel
            if any(base.id == 'BaseModel' for base in node.bases if hasattr(base, 'id')):
                schema = {
                    'name': node.name,
                    'description': ast.get_docstring(node),
                    'fields': []
                }
                
                # Extract fields
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        field = {
                            'name': item.target.id,
                            'type': ast.unparse(item.annotation),
                            'required': item.value is None,
                            'default': ast.unparse(item.value) if item.value else None
                        }
                        schema['fields'].append(field)
                        
                schemas.append(schema)
                
    return schemas
```

### 2. API Documentation Generation

Create comprehensive API documentation:

**OpenAPI/Swagger Generation**
```yaml
openapi: 3.0.0
info:
  title: ${API_TITLE}
  version: ${VERSION}
  description: |
    ${DESCRIPTION}
    
    ## Authentication
    ${AUTH_DESCRIPTION}
    
    ## Rate Limiting
    ${RATE_LIMIT_INFO}
    
  contact:
    email: ${CONTACT_EMAIL}
  license:
    name: ${LICENSE}
    url: ${LICENSE_URL}

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server

security:
  - bearerAuth: []
  - apiKey: []

paths:
  /users:
    get:
      summary: List all users
      description: |
        Retrieve a paginated list of users with optional filtering
      operationId: listUsers
      tags:
        - Users
      parameters:
        - name: page
          in: query
          description: Page number for pagination
          required: false
          schema:
            type: integer
            default: 1
            minimum: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
        - name: search
          in: query
          description: Search term for filtering users
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
              examples:
                success:
                  value:
                    data:
                      - id: "123"
                        email: "user@example.com"
                        name: "John Doe"
                    pagination:
                      page: 1
                      limit: 20
                      total: 100
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimitExceeded'

components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: string
          format: uuid
          description: Unique user identifier
        email:
          type: string
          format: email
          description: User's email address
        name:
          type: string
          description: User's full name
        createdAt:
          type: string
          format: date-time
          description: Account creation timestamp
```

**API Client SDK Documentation**
```python
"""
# API Client Documentation

## Installation

```bash
pip install your-api-client
```

## Quick Start

```python
from your_api import Client

# Initialize client
client = Client(api_key="your-api-key")

# List users
users = client.users.list(page=1, limit=20)

# Get specific user
user = client.users.get("user-id")

# Create user
new_user = client.users.create(
    email="user@example.com",
    name="John Doe"
)
```

## Authentication

The client supports multiple authentication methods:

### API Key Authentication

```python
client = Client(api_key="your-api-key")
```

### OAuth2 Authentication

```python
client = Client(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

## Error Handling

```python
from your_api.exceptions import APIError, RateLimitError

try:
    user = client.users.get("user-id")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except APIError as e:
    print(f"API error: {e.message}")
```

## Pagination

```python
# Automatic pagination
for user in client.users.list_all():
    print(user.email)

# Manual pagination
page = 1
while True:
    response = client.users.list(page=page)
    for user in response.data:
        print(user.email)
    
    if not response.has_next:
        break
    page += 1
```
"""
```

## Output Format

1. **API Documentation**: OpenAPI spec with interactive playground
2. **SDK Documentation**: Client libraries with authentication and error handling
3. **Schema Documentation**: Pydantic models and type definitions
4. **Endpoint Reference**: Complete API reference with examples

Focus on creating documentation that is accurate, comprehensive, and easy to maintain alongside backend code changes.
