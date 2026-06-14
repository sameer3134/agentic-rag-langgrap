---
description: "Frontend Testing Framework - JavaScript/TypeScript"
model: claude-sonnet-4-0
complexity: advanced
priority: critical
tags: ["testing", "frontend", "components"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Frontend Test Harness Generator

You are a testing expert specializing in creating comprehensive, maintainable, and efficient test suites for frontend applications. Design testing frameworks that cover unit, integration, end-to-end, and property-based testing with industry best practices for JavaScript and TypeScript.

## Context
The user needs a complete frontend testing strategy and implementation. Focus on creating a robust testing pyramid with appropriate tools, patterns, and automation that ensures code quality and reliability.

## Requirements
$ARGUMENTS

## Instructions

### 1. Testing Framework Selection (Frontend)

Choose appropriate testing frameworks based on frontend technology stack:

**Framework Selection Matrix**
```python
def select_testing_framework(tech_stack, project_type):
    """Select optimal testing frameworks based on frontend technology"""
    
    frameworks = {
        'javascript': {
            'unit_testing': 'jest, vitest',
            'mocking': 'jest, sinon',
            'property_testing': 'fast-check',
            'load_testing': 'artillery, k6',
            'contract_testing': 'pact-js',
            'security_testing': 'npm audit, snyk',
            'api_testing': 'supertest, axios',
            'e2e_testing': 'playwright, cypress'
        }
    }
    
    return frameworks.get(tech_stack, frameworks['javascript'])
```

### 2. JavaScript/TypeScript Testing Implementation

Complete JavaScript testing framework with Jest and Playwright:

**Jest Configuration**
```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/{{PATH_TESTS}}/**/*.+(ts|tsx|js)',
    '**/*.(test|spec).+(ts|tsx|js)'
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },
  collectCoverageFrom: [
    '{{PATH_SRC}}/**/*.{ts,tsx}',
    '!{{PATH_SRC}}/**/*.d.ts',
    '!{{PATH_SRC}}/types/**/*'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/{{PATH_TESTS}}/setup.ts'],
  testTimeout: 10000,
  maxWorkers: '50%'
};

// {{PATH_TESTS}}/setup.ts
import { jest } from '@jest/globals';

// Global test setup
beforeAll(async () => {
  // Setup test database
  // Initialize test services
});

afterAll(async () => {
  // Cleanup
});

beforeEach(() => {
  // Reset mocks
  jest.clearAllMocks();
});

// Global mocks
jest.mock('nodemailer', () => ({
  createTransport: jest.fn(() => ({
    sendMail: jest.fn().mockResolvedValue({ messageId: 'test-id' })
  }))
}));
```

**Unit Testing with Jest**
```typescript
// {{PATH_TESTS}}/unit/userService.test.ts
import { UserService } from '../../{{PATH_SRC}}/services/userService';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { jest } from '@jest/globals';

// Mock Prisma
jest.mock('@prisma/client');
const mockPrisma = {
  user: {
    create: jest.fn(),
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    update: jest.fn(),
    delete: jest.fn()
  }
};

describe('UserService', () => {
  let userService: UserService;
  
  beforeEach(() => {
    (PrismaClient as jest.MockedClass<typeof PrismaClient>).mockImplementation(() => mockPrisma as any);
    userService = new UserService();
  });
  
  describe('createUser', () => {
    it('should create user successfully', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'password123',
        fullName: 'Test User'
      };
      
      const mockUser = {
        id: '1',
        email: userData.email,
        username: userData.username,
        fullName: userData.fullName,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      mockPrisma.user.findFirst.mockResolvedValue(null);
      mockPrisma.user.create.mockResolvedValue(mockUser);
      
      // Act
      const result = await userService.createUser(userData);
      
      // Assert
      expect(result).toEqual(mockUser);
      expect(mockPrisma.user.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          email: userData.email,
          username: userData.username,
          fullName: userData.fullName,
          hashedPassword: expect.any(String),
          isActive: true
        })
      });
    });
    
    it('should throw error for duplicate email', async () => {
      // Arrange
      const userData = {
        email: 'existing@example.com',
        username: 'testuser',
        password: 'password123'
      };
      
      mockPrisma.user.findFirst.mockResolvedValue({ id: '1' });
      
      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects
        .toThrow('User with this email or username already exists');
    });
    
    it('should hash password before storing', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'plainpassword'
      };
      
      mockPrisma.user.findFirst.mockResolvedValue(null);
      mockPrisma.user.create.mockResolvedValue({} as any);
      
      // Spy on bcrypt
      const hashSpy = jest.spyOn(bcrypt, 'hash').mockResolvedValue('hashedpassword' as never);
      
      // Act
      await userService.createUser(userData);
      
      // Assert
      expect(hashSpy).toHaveBeenCalledWith(userData.password, 12);
      expect(mockPrisma.user.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          hashedPassword: 'hashedpassword'
        })
      });
    });
  });
  
  describe('authenticateUser', () => {
    it('should return token for valid credentials', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockUser = {
        id: '1',
        email,
        hashedPassword: 'hashedpassword'
      };
      
      mockPrisma.user.findUnique.mockResolvedValue(mockUser);
      jest.spyOn(bcrypt, 'compare').mockResolvedValue(true as never);
      
      // Act
      const result = await userService.authenticateUser(email, password);
      
      // Assert
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });
    
    it('should return null for invalid credentials', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'wrongpassword';
      
      mockPrisma.user.findUnique.mockResolvedValue(null);
      
      // Act
      const result = await userService.authenticateUser(email, password);
      
      // Assert
      expect(result).toBeNull();
    });
  });
});
```

**Property-Based Testing with fast-check**
```typescript
// {{PATH_TESTS}}/unit/userValidation.property.test.ts
import fc from 'fast-check';
import { validateEmail, validateUsername } from '../../{{PATH_SRC}}/utils/validation';

describe('User Validation - Property Tests', () => {
  describe('validateEmail', () => {
    it('should always return boolean', () => {
      fc.assert(fc.property(
        fc.emailAddress(),
        (email) => {
          const result = validateEmail(email);
          expect(typeof result).toBe('boolean');
        }
      ));
    });
    
    it('should accept valid email formats', () => {
      fc.assert(fc.property(
        fc.emailAddress(),
        (email) => {
          expect(validateEmail(email)).toBe(true);
        }
      ));
    });
    
    it('should reject strings without @ symbol', () => {
      fc.assert(fc.property(
        fc.string().filter(s => !s.includes('@')),
        (invalidEmail) => {
          expect(validateEmail(invalidEmail)).toBe(false);
        }
      ));
    });
  });
  
  describe('validateUsername', () => {
    it('should accept alphanumeric strings of valid length', () => {
      fc.assert(fc.property(
        fc.string({ minLength: 3, maxLength: 30 })
          .filter(s => /^[a-zA-Z0-9]+$/.test(s)),
        (username) => {
          expect(validateUsername(username)).toBe(true);
        }
      ));
    });
    
    it('should reject strings that are too short or too long', () => {
      fc.assert(fc.property(
        fc.oneof(
          fc.string({ maxLength: 2 }),
          fc.string({ minLength: 31 })
        ),
        (username) => {
          expect(validateUsername(username)).toBe(false);
        }
      ));
    });
  });
});
```

## Related Templates

<!-- For backend (Python/Go/Java) testing, see: backend/test-harness.md -->
<!-- For CI/CD test integration, see: cloud/test-harness.md -->
<!-- For test data management and cross-command orchestration, see: general/test-harness.md -->
