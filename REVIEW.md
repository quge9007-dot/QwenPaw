# User Management System — Review Profile

## Project Overview
Spring Boot + MyBatis user management system supporting user CRUD, tag management, tag binding, and tag-based user matching.

## Architecture
- **Layer**: Controller → Service → Mapper → DB
- **ORM**: MyBatis (XML mappers)
- **Build**: Maven
- **Testing**: JUnit 5 + Mockito + AssertJ

## Key Modules
1. **User Management** — User CRUD with tag binding
2. **Tag Management** — Tag CRUD with categories
3. **Tag Matching** — Match users by tag IDs
4. **User Groups** — Group management with tag associations
5. **Tag Binding** — User-tag binding relationships

## Gates (per crate)

### api/ (Controllers)
- Must use `@Valid` on request body parameters
- Must return structured response with errorCode/errorMessage
- Must delegate business logic to service layer

### service/ (Services)
- Must not duplicate business logic across services
- Must complete transactional operations atomically
- Error codes must be unique per error condition

### dao/mapper/ (Data Access)
- Mapper method names must match XML statement IDs
- ResultMaps must not have duplicate column mappings
- SQL must use parameter binding (`#{}`) not string concatenation

### common/ (Shared)
- ErrorCode enum values must be unique across the system
- Constants must cover all magic values
- BaseEntity must be used consistently for auto-fill fields

### model/ (DTO/Request)
- DTOs must map cleanly to/from DO entities
- Request objects must have proper validation annotations
