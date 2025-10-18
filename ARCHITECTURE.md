# Vismaya DemandOps - Architecture Overview

## SOLID Principles Implementation

This project follows SOLID principles for maintainable, scalable, and testable code:

### 1. Single Responsibility Principle (SRP)
- Each class has one reason to change
- `CostAnalysisService` - handles cost analysis only
- `ResourceManagementService` - handles resource inventory only
- `AWSCostProvider` - handles cost data retrieval only

### 2. Open/Closed Principle (OCP)
- Classes are open for extension, closed for modification
- New cost providers can be added without changing existing code
- New AI assistants can be plugged in via interfaces

### 3. Liskov Substitution Principle (LSP)
- Implementations can be substituted without breaking functionality
- `BedrockAIAssistant` can be replaced with `OpenAIAssistant`
- `AWSCostProvider` can be replaced with `MockCostProvider`

### 4. Interface Segregation Principle (ISP)
- Interfaces are focused and specific
- `ICostDataProvider` - only cost-related methods
- `IResourceProvider` - only resource-related methods
- `IAIAssistant` - only AI-related methods

### 5. Dependency Inversion Principle (DIP)
- High-level modules don't depend on low-level modules
- Services depend on interfaces, not concrete implementations
- Dependency injection container manages all dependencies

## Project Structure

```
vismaya-demandops/
├── src/
│   ├── core/                    # Domain layer (business logic)
│   │   ├── models.py           # Domain entities and value objects
│   │   └── interfaces.py       # Abstract interfaces
│   │
│   ├── application/            # Application layer (use cases)
│   │   ├── use_cases.py        # Business use cases
│   │   └── dependency_injection.py  # DI container
│   │
│   ├── services/               # Application services
│   │   ├── cost_service.py     # Cost analysis orchestration
│   │   └── resource_service.py # Resource management
│   │
│   └── infrastructure/         # Infrastructure layer (external services)
│       ├── aws_cost_provider.py      # AWS Cost Explorer integration
│       ├── aws_resource_provider.py  # AWS EC2/RDS integration
│       ├── bedrock_ai_assistant.py   # AWS Bedrock integration
│       └── aws_session_factory.py    # AWS authentication
│
├── dashboard.py                # Presentation layer (Streamlit UI)
├── app.py                     # Application entry point
├── config.py                  # Configuration management
└── requirements.txt           # Dependencies
```

## Layer Responsibilities

### 1. Core Layer (`src/core/`)
- **Purpose**: Contains business entities and rules
- **Dependencies**: None (pure business logic)
- **Key Files**:
  - `models.py`: Domain entities (CostData, EC2Instance, etc.)
  - `interfaces.py`: Abstract contracts for external services

### 2. Application Layer (`src/application/`)
- **Purpose**: Orchestrates business workflows
- **Dependencies**: Core layer only
- **Key Files**:
  - `use_cases.py`: Business use cases (GetUsageSummary, AnalyzeScenario)
  - `dependency_injection.py`: Manages object creation and dependencies

### 3. Services Layer (`src/services/`)
- **Purpose**: Application-specific business logic
- **Dependencies**: Core layer and interfaces
- **Key Files**:
  - `cost_service.py`: Cost analysis and forecasting
  - `resource_service.py`: Resource inventory management

### 4. Infrastructure Layer (`src/infrastructure/`)
- **Purpose**: External service integrations
- **Dependencies**: Core interfaces
- **Key Files**:
  - `aws_cost_provider.py`: AWS Cost Explorer client
  - `aws_resource_provider.py`: AWS EC2/RDS clients
  - `bedrock_ai_assistant.py`: AWS Bedrock AI client

### 5. Presentation Layer
- **Purpose**: User interface and interaction
- **Dependencies**: Application layer use cases
- **Key Files**:
  - `dashboard.py`: Streamlit web interface
  - `app.py`: Application bootstrap

## Design Patterns Used

### 1. Repository Pattern
- `ICostDataProvider`, `IResourceProvider` abstract data access
- Implementations handle specific data sources (AWS, mock data)

### 2. Factory Pattern
- `AWSSessionFactory` creates AWS sessions with proper authentication
- Handles different authentication methods (SSO, credentials)

### 3. Dependency Injection
- `DependencyContainer` manages object lifecycle
- Enables easy testing and configuration changes

### 4. Use Case Pattern
- Each business operation is a separate use case class
- Clear separation of business logic from presentation

### 5. Strategy Pattern
- Different AI assistants can be plugged in
- Different cost providers can be used

## Benefits of This Architecture

### 1. Testability
- Each layer can be tested independently
- Mock implementations for external services
- Clear separation of concerns

### 2. Maintainability
- Changes in one layer don't affect others
- Easy to add new features or modify existing ones
- Clear code organization

### 3. Scalability
- Easy to add new AWS services
- Can plug in different AI providers
- Modular architecture supports growth

### 4. Flexibility
- Can switch between AWS SSO and credentials
- Can use mock data for development
- Easy to add new cost providers

## Usage Examples

### Adding a New Cost Provider
```python
class AzureCostProvider(ICostDataProvider):
    async def get_current_costs(self) -> CostData:
        # Azure-specific implementation
        pass
```

### Adding a New Use Case
```python
class OptimizeResourcesUseCase:
    def __init__(self, resource_service: ResourceManagementService):
        self._resource_service = resource_service
    
    async def execute(self) -> List[OptimizationAction]:
        # Business logic for resource optimization
        pass
```

### Testing with Mocks
```python
class MockCostProvider(ICostDataProvider):
    async def get_current_costs(self) -> CostData:
        return CostData(amount=1000.0)

# Use in tests
container = DependencyContainer(test_config)
container._services['cost_provider'] = MockCostProvider()
```

This architecture ensures the codebase is maintainable, testable, and ready for future enhancements while following industry best practices.

---

This comprehensive deployment guide ensures your Vismaya DemandOps application runs securely and efficiently in production environments.

## Team

**Team MaximAI** - Passionate about AI-driven solutions for cloud cost optimization

### Our Mission
To democratize cloud cost optimization through intelligent AI-powered solutions that make FinOps accessible to organizations of all sizes.

## License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**