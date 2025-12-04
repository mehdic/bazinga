---
name: grpc
type: api
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# gRPC Engineering Expertise

## Specialist Profile
gRPC specialist building high-performance services. Expert in Protocol Buffers, streaming, and service mesh patterns.

## Implementation Guidelines

### Protocol Buffers

```protobuf
// proto/user/v1/user.proto
syntax = "proto3";

package user.v1;

option go_package = "github.com/mycompany/api/gen/user/v1;userv1";

import "google/protobuf/timestamp.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
  rpc StreamUsers(StreamUsersRequest) returns (stream User);
}

message User {
  string id = 1;
  string email = 2;
  string display_name = 3;
  UserStatus status = 4;
  google.protobuf.Timestamp created_at = 5;
}

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_INACTIVE = 2;
  USER_STATUS_PENDING = 3;
}

message GetUserRequest {
  string id = 1;
}

message GetUserResponse {
  User user = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  UserStatus status_filter = 3;
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}

message CreateUserRequest {
  string email = 1;
  string display_name = 2;
}

message CreateUserResponse {
  User user = 1;
}
```

### Go Server Implementation

```go
// internal/service/user.go
type UserServer struct {
    userv1.UnimplementedUserServiceServer
    repo UserRepository
}

func (s *UserServer) GetUser(ctx context.Context, req *userv1.GetUserRequest) (*userv1.GetUserResponse, error) {
    user, err := s.repo.FindByID(ctx, req.Id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, status.Error(codes.NotFound, "user not found")
        }
        return nil, status.Error(codes.Internal, "failed to fetch user")
    }
    return &userv1.GetUserResponse{User: toProto(user)}, nil
}

func (s *UserServer) StreamUsers(req *userv1.StreamUsersRequest, stream userv1.UserService_StreamUsersServer) error {
    users, err := s.repo.FindAll(stream.Context())
    if err != nil {
        return status.Error(codes.Internal, "failed to fetch users")
    }

    for _, user := range users {
        if err := stream.Send(toProto(user)); err != nil {
            return err
        }
    }
    return nil
}
```

### Client Usage

```go
// cmd/client/main.go
func main() {
    conn, err := grpc.Dial(
        "localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer conn.Close()

    client := userv1.NewUserServiceClient(conn)

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    resp, err := client.GetUser(ctx, &userv1.GetUserRequest{Id: "123"})
    if err != nil {
        st, ok := status.FromError(err)
        if ok && st.Code() == codes.NotFound {
            log.Println("User not found")
            return
        }
        log.Fatal(err)
    }

    fmt.Printf("User: %v\n", resp.User)
}
```

## Patterns to Avoid
- ❌ Ignoring error codes
- ❌ Missing deadlines/timeouts
- ❌ Large messages (>4MB default)
- ❌ Blocking in stream handlers

## Verification Checklist
- [ ] Proper error codes
- [ ] Context propagation
- [ ] Streaming for large datasets
- [ ] Proto versioning (v1, v2)
- [ ] Interceptors for cross-cutting
