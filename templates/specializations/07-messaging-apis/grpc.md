---
name: grpc
type: api
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# gRPC Engineering Expertise

## Specialist Profile
gRPC specialist building high-performance services. Expert in Protocol Buffers, streaming, and service mesh patterns.

---

## Patterns to Follow

### Proto Design
- **Package versioning**: `package user.v1;`
- **Service per domain**: UserService, OrderService
- **Request/Response pattern**: Separate messages
- **Enums with UNSPECIFIED = 0**: Default/unknown state
- **google.protobuf types**: Timestamp, Duration, Struct

### Error Handling
- **Standard status codes**: NotFound, InvalidArgument, Internal
- **Rich error details**: google.rpc.Status with details
- **Error messages for humans**: Clear, actionable
- **Don't leak internals**: Abstract error messages

### Streaming Patterns
- **Server streaming**: Large result sets
- **Client streaming**: Uploads, aggregation
- **Bidirectional**: Real-time, chat
- **Backpressure handling**: Flow control

### Context & Deadlines
- **Always set deadlines**: Prevent resource exhaustion
- **Propagate context**: Across service calls
- **Cancel on timeout**: Client and server
- **Metadata for context**: Auth, tracing, request ID

### Interceptors
- **Unary interceptors**: Logging, auth, metrics
- **Stream interceptors**: Same for streaming
- **Order matters**: Auth before logging
- **Recovery interceptor**: Catch panics (Go)

### Health Checks
- **gRPC Health Checking Protocol**: Standard service
- **Serving status**: SERVING, NOT_SERVING
- **Per-service status**: Fine-grained health
- **Kubernetes integration**: liveness/readiness probes

### gRPC Version Features
<!-- version: grpc >= 1.50 -->
- **xDS support**: Service mesh integration
- **gRPC-JSON transcoding**: REST-compatible endpoints
<!-- version: grpc >= 1.55 -->
- **OpenTelemetry native**: Built-in observability
<!-- version: protobuf >= 3.21 -->
- **Edition syntax**: New proto syntax (replaces proto3 features)
- **Editions tooling**: Migrate from proto2/proto3

---

## Patterns to Avoid

### Proto Anti-Patterns
- ❌ **No package versioning**: Breaking changes affect all
- ❌ **Reusing field numbers**: Wire format corruption
- ❌ **required fields (proto2)**: Use proto3
- ❌ **Giant messages**: Keep under 4MB

### Error Anti-Patterns
- ❌ **Ignoring error codes**: Treat all as generic error
- ❌ **Internal details in messages**: Security leak
- ❌ **Wrong status code**: NotFound for validation error
- ❌ **Empty error messages**: Unhelpful

### Performance Anti-Patterns
- ❌ **Missing deadlines**: Runaway requests
- ❌ **Blocking in stream handlers**: Reduces throughput
- ❌ **Large message without streaming**: Memory pressure
- ❌ **No connection pooling**: Connection overhead

### Design Anti-Patterns
- ❌ **REST semantics in gRPC**: Use native patterns
- ❌ **No interceptors**: Cross-cutting concerns scattered
- ❌ **Synchronous when async fits**: Blocking unnecessarily
- ❌ **Ignoring context cancellation**: Resource waste

---

## Verification Checklist

### Proto
- [ ] Package versioning (v1, v2)
- [ ] Enums start with UNSPECIFIED
- [ ] Standard types used
- [ ] Documentation comments

### Implementation
- [ ] Proper status codes
- [ ] Deadlines set on all calls
- [ ] Context propagation
- [ ] Interceptors for cross-cutting

### Streaming
- [ ] Used for large data sets
- [ ] Backpressure handled
- [ ] Errors sent properly
- [ ] Graceful completion

### Operations
- [ ] Health service implemented
- [ ] Metrics exposed
- [ ] Tracing integrated
- [ ] Load balancing configured

---

## Code Patterns (Reference)

### Proto
- **Service**: `service UserService { rpc GetUser(GetUserRequest) returns (GetUserResponse); }`
- **Streaming**: `rpc StreamUsers(StreamRequest) returns (stream User);`
- **Message**: `message User { string id = 1; string email = 2; UserStatus status = 3; }`
- **Enum**: `enum UserStatus { USER_STATUS_UNSPECIFIED = 0; USER_STATUS_ACTIVE = 1; }`

### Server (Go)
- **Error**: `return nil, status.Error(codes.NotFound, "user not found")`
- **Rich error**: `status.Errorf(codes.InvalidArgument, "validation failed").WithDetails(...)`
- **Stream send**: `for _, user := range users { stream.Send(toProto(user)) }`

### Client (Go)
- **With deadline**: `ctx, cancel := context.WithTimeout(ctx, 5*time.Second); defer cancel()`
- **Error handling**: `if st, ok := status.FromError(err); ok && st.Code() == codes.NotFound { ... }`
- **Interceptor**: `grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor())`

### Health Check
- **Service**: `grpc_health_v1.RegisterHealthServer(s, health.NewServer())`
- **Set status**: `healthServer.SetServingStatus("user.v1.UserService", healthpb.HealthCheckResponse_SERVING)`

