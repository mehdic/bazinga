---
name: elixir
type: language
priority: 1
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Elixir Engineering Expertise

## Specialist Profile
Elixir specialist building fault-tolerant systems. Expert in OTP, pattern matching, and the BEAM ecosystem.

## Implementation Guidelines

### Modules and Structs

```elixir
defmodule User do
  @enforce_keys [:id, :email]
  defstruct [:id, :email, :display_name, :created_at]

  @type t :: %__MODULE__{
    id: String.t(),
    email: String.t(),
    display_name: String.t() | nil,
    created_at: DateTime.t() | nil
  }

  def new(attrs) do
    %__MODULE__{
      id: attrs.id,
      email: attrs.email,
      display_name: attrs[:display_name],
      created_at: DateTime.utc_now()
    }
  end
end
```

### Pattern Matching

```elixir
def handle_result({:ok, user}), do: process_user(user)
def handle_result({:error, reason}), do: log_error(reason)

def greet(%User{display_name: name}) when not is_nil(name) do
  "Hello, #{name}!"
end
def greet(%User{email: email}), do: "Hello, #{email}!"
```

### Pipe Operator

```elixir
def get_active_users do
  User
  |> Repo.all()
  |> Enum.filter(&(&1.status == :active))
  |> Enum.sort_by(& &1.created_at, {:desc, DateTime})
  |> Enum.map(&to_dto/1)
end
```

### With Statement

```elixir
def create_user(params) do
  with {:ok, validated} <- validate(params),
       {:ok, user} <- Repo.insert(User.new(validated)),
       :ok <- send_welcome_email(user) do
    {:ok, user}
  else
    {:error, %Ecto.Changeset{} = changeset} ->
      {:error, format_errors(changeset)}
    {:error, reason} ->
      {:error, reason}
  end
end
```

### GenServer

```elixir
defmodule UserCache do
  use GenServer

  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, %{}, opts)
  end

  def get(pid, key), do: GenServer.call(pid, {:get, key})
  def put(pid, key, value), do: GenServer.cast(pid, {:put, key, value})

  @impl true
  def init(state), do: {:ok, state}

  @impl true
  def handle_call({:get, key}, _from, state) do
    {:reply, Map.get(state, key), state}
  end
end
```

## Patterns to Avoid
- ❌ Nested case statements (use with)
- ❌ Long function bodies
- ❌ Ignoring OTP patterns
- ❌ Not using supervision trees

## Verification Checklist
- [ ] Pattern matching used
- [ ] Pipe operator for transforms
- [ ] GenServer for stateful processes
- [ ] Proper supervision
- [ ] Dialyzer types
