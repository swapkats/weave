# Code Review Checklist

A comprehensive guide for reviewing code quality, security, and best practices.

## Code Quality

### Readability
- [ ] Variable and function names are clear and descriptive
- [ ] Code is self-documenting with minimal comments
- [ ] Comments explain "why" not "what"
- [ ] Consistent formatting and style throughout
- [ ] No unnecessary complexity

### Structure & Design
- [ ] Functions are small and focused (< 20 lines ideal)
- [ ] Single Responsibility Principle followed
- [ ] DRY - no duplicate code
- [ ] Proper separation of concerns
- [ ] Appropriate use of design patterns

### Error Handling
- [ ] Input validation at boundaries
- [ ] Proper exception handling (no empty catches)
- [ ] Meaningful error messages
- [ ] Edge cases handled explicitly
- [ ] Graceful degradation where appropriate

## Functionality

### Correctness
- [ ] Implements all requirements correctly
- [ ] Logic is sound and bug-free
- [ ] Edge cases covered
- [ ] No off-by-one errors
- [ ] Proper null/undefined handling

### Performance
- [ ] No obvious performance issues
- [ ] Appropriate algorithm complexity
- [ ] No unnecessary loops or operations
- [ ] Efficient data structures used
- [ ] Database queries optimized (if applicable)

## Security

### Input Validation
- [ ] All user input validated and sanitized
- [ ] Type checking for function parameters
- [ ] Length/range validation applied
- [ ] Whitelist approach for validation

### Common Vulnerabilities (OWASP Top 10)
- [ ] **SQL Injection**: Parameterized queries used
- [ ] **XSS**: Output encoding applied
- [ ] **CSRF**: Anti-CSRF tokens implemented
- [ ] **Authentication**: Proper auth checks
- [ ] **Authorization**: Access control enforced
- [ ] **Sensitive Data**: Encrypted at rest and in transit
- [ ] **Security Misconfig**: No default credentials
- [ ] **Deserialization**: Safe deserialization practices
- [ ] **Logging**: No sensitive data in logs
- [ ] **Dependencies**: No known vulnerabilities

### Secrets Management
- [ ] No hardcoded passwords or API keys
- [ ] Secrets stored in environment variables
- [ ] No sensitive data in version control
- [ ] Proper key rotation mechanisms

## Testing

### Test Coverage
- [ ] Unit tests for core functionality
- [ ] Integration tests for critical paths
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Coverage > 80% for new code

### Test Quality
- [ ] Tests are clear and maintainable
- [ ] Descriptive test names
- [ ] Arrange-Act-Assert pattern
- [ ] No flaky tests
- [ ] Tests run fast (unit tests < 100ms)

## Documentation

### Code Documentation
- [ ] Public APIs have docstrings
- [ ] Complex logic explained
- [ ] Type hints included (Python/TypeScript)
- [ ] Examples provided for non-obvious usage

### Project Documentation
- [ ] README updated if needed
- [ ] API documentation current
- [ ] Architecture diagrams accurate
- [ ] Migration guides for breaking changes

## Review Severity Levels

### Critical
- Security vulnerabilities
- Data loss risks
- Breaking changes to APIs
- Performance regressions (> 20%)

### Major
- Logic errors
- Missing error handling
- Poor code structure
- Inadequate test coverage

### Minor
- Style inconsistencies
- Missing documentation
- Minor optimizations
- Naming improvements

## Review Outcome

After review, provide:

1. **Overall Quality Score**: 1-10
2. **Strengths**: What was done well
3. **Issues**: Categorized by severity
4. **Suggestions**: Improvement opportunities
5. **Approval Status**:
   - ✅ Approved
   - 🔄 Changes Requested
   - ❌ Rejected

## Good Review Practices

- Be constructive and specific
- Praise good work
- Ask questions rather than demand changes
- Focus on important issues
- Suggest alternatives, don't just criticize
- Consider the context and constraints
