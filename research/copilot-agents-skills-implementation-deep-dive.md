# GitHub Copilot Sub-Agents & Skills: Implementation Deep Dive

**Date:** 2025-01-23
**Context:** Technical analysis of GitHub Copilot's sub-agent and skills architecture for potential BAZINGA integration
**Decision:** Pending user review
**Status:** Reviewed
**Reviewed by:** Google Gemini (via octo:debate), Claude (cross-verification), Web Sources

---

## Executive Summary

This document provides an exhaustive technical analysis of GitHub Copilot's sub-agent and skills systems in VS Code, examining every architectural component from YAML frontmatter parsing to inter-agent communication protocols. The analysis covers:

1. **Four-tier agent architecture** (Local, Background, Cloud, Third-party)
2. **Three-level skill loading system** (Discovery → Instructions → Resources)
3. **Chat Participant API** for extension-based agents
4. **Language Model Tool API** for custom tools
5. **MCP integration** for external services
6. **Handoff mechanisms** for agent-to-agent delegation
7. **Internal prompt engineering** (3-layer system prompt structure)

---

## Table of Contents

1. [Agent Architecture Overview](#1-agent-architecture-overview)
2. [Sub-Agent System Deep Dive](#2-sub-agent-system-deep-dive)
3. [Skills System Technical Specification](#3-skills-system-technical-specification)
4. [Chat Participant API Internals](#4-chat-participant-api-internals)
5. [Language Model Tool API](#5-language-model-tool-api)
6. [MCP Server Integration](#6-mcp-server-integration)
7. [Internal Prompt Engineering](#7-internal-prompt-engineering)
8. [Handoffs and Delegation](#8-handoffs-and-delegation)
9. [Security Model](#9-security-model)
10. [Comparison to Claude Code/BAZINGA](#10-comparison-to-claude-codebazinga)
11. [Critical Analysis](#11-critical-analysis)
12. [Implementation Recommendations](#12-implementation-recommendations)

---

## 1. Agent Architecture Overview

### 1.1 Four-Tier Agent Hierarchy

GitHub Copilot implements a four-tier agent system with distinct execution environments:

| Tier | Agent Type | Execution Environment | Context Access | Tool Access | MCP Support |
|------|-----------|----------------------|----------------|-------------|-------------|
| 1 | **Local Agents** | VS Code process | Full workspace + runtime | All configured | Yes (local) |
| 2 | **Background Agents** | CLI, isolated worktree | Explicit only | Terminal only | No |
| 3 | **Cloud Agents** | GitHub infrastructure | Branch/PR isolated | Remote MCP only | Yes (remote) |
| 4 | **Third-party Agents** | Provider-dependent | Provider-dependent | Varies | No |

### 1.2 Agent Execution Contexts

#### Local Agents
- Run interactively within VS Code
- Full access to:
  - Editor state (selections, diagnostics)
  - Workspace files and structure
  - Terminal output and test results
  - All VS Code extension APIs
  - MCP servers and extension-provided tools
- Support custom agent configurations (`.agent.md` files)

#### Background Agents (Copilot CLI)
- Run non-interactively via CLI
- Execute in isolated Git worktrees
- **Cannot access:**
  - VS Code built-in tools
  - Runtime context (failed tests, selections)
  - MCP servers
  - Extension-provided tools
- Limited to CLI-available models

#### Cloud Agents (Copilot Coding Agent)
- Run on GitHub's infrastructure
- Operate in sandboxed environments with:
  - Read-only repository access
  - Firewall-controlled internet access
  - Branch/PR isolation
- Access remote MCP servers only
- Create PRs for code changes

#### Third-Party Agents
- Integrated via VS Code's unified agent interface
- Examples: OpenAI Codex
- Tool/model access determined by provider

### 1.3 Agent Discovery and Registration

Agents are discovered from multiple locations:

```
Priority Order (lowest wins for deduplication):
1. Organization-level custom agents
2. Repository-level custom agents (./github/agents/*.agent.md)
3. User profile agents
4. Extension-provided agents
```

---

## 2. Sub-Agent System Deep Dive

### 2.1 What is a Sub-Agent?

A **Context-Isolated Sub-Agent** is an autonomous agent invoked within a main chat session with its own isolated context window. Key characteristics:

- **Context Isolation:** Own context window independent from parent session
- **Worktree Isolation:** Operates in separate Git worktree (optional)
- **No Nesting:** Cannot invoke another sub-agent (single-level only)
- **Inheritance:** Can inherit or override parent agent configuration

### 2.2 Sub-Agent Invocation Mechanisms

#### Explicit Invocation via `#runSubagent`
```
User prompt: "Research the authentication patterns in this codebase #runSubagent"
```

The `#runSubagent` tool reference triggers:
1. VS Code spawns new isolated context
2. Optional worktree creation
3. Sub-agent receives sanitized context from parent
4. Autonomous execution until completion/timeout
5. Results returned to parent session

#### Automatic Invocation
Copilot may suggest sub-agent usage automatically for:
- Complex multi-step research tasks
- Tasks requiring isolated file modifications
- Long-running operations benefiting from isolation

#### Custom Agent Reference
```
User prompt: "@research-agent analyze the API design patterns"
```

### 2.2.1 Enabling `#runSubagent` in Custom Agents

To enable an agent to spawn sub-agents, add `runSubagent` to the `tools` frontmatter:

```yaml
---
name: orchestrator
description: Coordinates multi-agent workflows
tools:
  - runSubagent    # Enables programmatic sub-agent spawning
  - read
  - edit
---
```

### 2.2.2 Programmatic Invocation Patterns

**Pattern 1: Tool Reference in Output**
```
# Agent can output:
"Evaluate the #file:auth.py using #runSubagent and generate a security report"
```

**Pattern 2: Natural Language Delegation**
```
# Agent can output:
"Use the @project-manager subagent to analyze requirements"
"Delegate implementation to the @developer agent"
```

**Pattern 3: Direct Tool Call**
```
# Agent can output:
"Use the testing subagent to write unit tests for the authentication module"
```

**Automatic Delegation:** If the agent has `runSubagent` enabled, Copilot will automatically:
1. Analyze the request description
2. Match against available custom agents' `description` fields
3. Choose and invoke the most appropriate sub-agent

### 2.2.3 Execution Model (UPDATED Jan 23, 2026)

**Parallel Execution NOW SUPPORTED:** [PR #2839](https://github.com/microsoft/vscode-copilot-chat/pull/2839) merged January 15, 2026.

**Rule:** Multiple `#runSubagent` calls in the **same response block** execute in **parallel**.

```xml
<!-- PARALLEL: Same block = concurrent execution -->
<tool_calls>
  <runSubagent agent="@dev1" prompt="Implement module A" />
  <runSubagent agent="@dev2" prompt="Implement module B" />
  <runSubagent agent="@dev3" prompt="Implement module C" />
</tool_calls>
<!-- All 3 run SIMULTANEOUSLY -->

<!-- SERIAL: Separate blocks = sequential execution -->
<tool_calls><runSubagent agent="@dev1" /></tool_calls>
<!-- wait for result -->
<tool_calls><runSubagent agent="@dev2" /></tool_calls>
<!-- wait for result -->
```

**Feature Status:** [Issue #274630](https://github.com/microsoft/vscode/issues/274630) - **CLOSED as COMPLETED**

### 2.3 Context Window Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN SESSION                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Context Window (64k-128k tokens)                │    │
│  │ - User prompts                                   │    │
│  │ - Workspace structure                            │    │
│  │ - Tool definitions                               │    │
│  │ - Conversation history                           │    │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│                    spawn  │  return                      │
│                           ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │            SUB-AGENT SESSION                     │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │ Isolated Context Window (64k tokens)    │    │    │
│  │  │ - Sanitized parent context              │    │    │
│  │  │ - Own tool definitions                  │    │    │
│  │  │ - Own conversation history              │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │              │                                   │    │
│  │              │ (isolated worktree)               │    │
│  │              ▼                                   │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │ Git Worktree                            │    │    │
│  │  │ - Separate folder                       │    │    │
│  │  │ - Independent file changes              │    │    │
│  │  │ - Protected from main workspace         │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 2.4 Context Window Limits and Management

| Environment | Token Limit | Auto-compaction Trigger |
|-------------|-------------|-------------------------|
| github.com, CLI, most IDEs | 64k tokens | 95% capacity |
| VS Code Insiders | 128k tokens | 95% capacity |

> **Note:** These token limits are approximate and may vary by model. The landscape of context windows is evolving rapidly, and exact figures are subject to change.

**Token Management Strategies:**
1. **Warning at 80%:** User notified of approaching limit
2. **Auto-compaction at 95%:** Conversation history compressed
3. **Repo-aware retrieval:** Large repos use embeddings instead of full context
4. **Lazy skill loading:** Only load skill bodies when matched
5. **Tool result truncation:** Large outputs summarized

### 2.5 Sub-Agent Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ SPAWN        │────▶│ EXECUTE      │────▶│ ITERATE      │
│              │     │              │     │              │
│ - Create ctx │     │ - Tool calls │     │ - Error check│
│ - Init tools │     │ - File edits │     │ - Self-fix   │
│ - Setup wktr │     │ - Commands   │     │ - Re-execute │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌──────────────┐             │
                     │ COMPLETION   │◀────────────┘
                     │              │
                     │ - Return     │
                     │ - Merge/Disc │
                     │ - Archive    │
                     └──────────────┘
```

**Timeout Behavior:**
- Sessions timeout after 1 hour if stuck
- Built-in retry mechanism: 5 attempts with 5-second intervals

### 2.6 Git Worktree Implementation

When worktree isolation is enabled:

1. **Creation:** VS Code creates `<repo>/.git/worktrees/<session-id>/`
2. **Isolation:** All file changes happen in worktree, not main workspace
3. **Concurrency:** Multiple background agents can run simultaneously without conflicts
4. **Review:** User can view diffs via "View All Edits"
5. **Merge:** "Apply" action merges worktree changes to main workspace
6. **Cleanup:** Worktree deleted after session ends or changes applied

---

## 3. Skills System Technical Specification

### 3.1 SKILL.md File Format

Skills are defined in Markdown files with YAML frontmatter:

```yaml
---
# REQUIRED FIELDS
name: "skill-identifier"        # Lowercase, hyphens, max 64 chars
description: |                  # When to use, max 1024 chars
  Performs X when user asks about Y.
  Activates for requests involving Z patterns.

# OPTIONAL FIELDS
license: "MIT"                  # License information
---

# Skill Title

## Purpose
What this skill accomplishes.

## When to Use
- Scenario 1
- Scenario 2

## Instructions

### Step 1: Analysis
Analyze the request...

### Step 2: Execution
1. Check [template](./templates/main.template)
2. Run [script](./scripts/helper.sh)

## Examples

### Example 1
Input: "Do X"
Output: "Result Y"

## Resources
- [Config Schema](./schemas/config.json)
```

### 3.2 Directory Structure

```
.github/skills/                  # Project skills (PRIMARY)
├── webapp-testing/
│   ├── SKILL.md                 # Required: skill definition
│   ├── test-template.js         # Optional: bundled script
│   ├── templates/               # Optional: templates
│   │   └── test-config.json
│   ├── scripts/                 # Optional: scripts
│   │   └── setup.sh
│   └── examples/                # Optional: examples
│       └── sample-output.md

.claude/skills/                  # Legacy location (backward compat)
└── <skill-name>/
    └── SKILL.md

~/.copilot/skills/               # Personal skills (cross-project)
└── my-global-skill/
    └── SKILL.md

~/.claude/skills/                # Legacy personal location
└── <skill-name>/
    └── SKILL.md
```

### 3.3 Three-Level Loading System

Copilot implements progressive skill loading to minimize context consumption:

```
┌────────────────────────────────────────────────────────────┐
│ LEVEL 1: DISCOVERY (Always Active)                         │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Copilot reads YAML frontmatter ONLY:                │    │
│ │   - name: "webapp-testing"                          │    │
│ │   - description: "Tests web applications..."        │    │
│ │                                                     │    │
│ │ Builds internal skill registry:                     │    │
│ │   { "webapp-testing": { desc: "...", path: "..." } }│    │
│ └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│                    prompt matches                           │
│                           ▼                                 │
├────────────────────────────────────────────────────────────┤
│ LEVEL 2: INSTRUCTIONS (On Demand)                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Full SKILL.md body loads into context:              │    │
│ │   - Purpose section                                 │    │
│ │   - When to Use section                             │    │
│ │   - Instructions section                            │    │
│ │   - Examples section                                │    │
│ │                                                     │    │
│ │ Supporting files NOT loaded yet                     │    │
│ └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│                    Copilot references file                  │
│                           ▼                                 │
├────────────────────────────────────────────────────────────┤
│ LEVEL 3: RESOURCES (On Reference)                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Individual files load when Copilot references them: │    │
│ │   - [script](./helper.sh) → loads helper.sh         │    │
│ │   - [template](./main.json) → loads main.json       │    │
│ │                                                     │    │
│ │ Files load individually, not entire directory       │    │
│ └─────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 3.4 Skill Activation Mechanism

Skills activate **automatically** based on semantic matching:

1. User sends prompt
2. Copilot compares prompt against all skill descriptions
3. Matching skills have their Level 2 content (SKILL.md body) injected
4. As Copilot processes, it may reference Level 3 resources

**No manual skill selection required.**

### 3.5 Skillsets (API-Based Skills)

For Copilot Extensions, skills can be defined via API endpoints:

```json
{
  "name": "Get Issues",
  "inference_description": "Searches for issues matching criteria",
  "endpoint": "https://api.example.com/issues",
  "parameters": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": ["open", "closed", "all"]
      },
      "labels": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "required": ["status"]
  }
}
```

**Skillset Requirements:**
- Maximum 5 skills per skillset
- Endpoint must accept POST with `application/json`
- Must verify GitHub signature for authentication
- Returns JSON consumed by Copilot

---

## 4. Chat Participant API Internals

### 4.1 Registration in package.json

```json
{
  "contributes": {
    "chatParticipants": [
      {
        "id": "extension.myParticipant",
        "name": "myassistant",
        "fullName": "My AI Assistant",
        "description": "Helps with domain-specific tasks",
        "isSticky": true
      }
    ],
    "commands": [
      {
        "name": "analyze",
        "description": "Analyze code structure"
      },
      {
        "name": "generate",
        "description": "Generate boilerplate"
      }
    ],
    "disambiguation": [
      {
        "category": "codeAnalysis",
        "description": "User wants code analyzed",
        "examples": [
          "analyze this code",
          "what does this function do",
          "explain this class"
        ]
      }
    ]
  }
}
```

### 4.2 ChatRequest Object

```typescript
interface ChatRequest {
  // User's natural language input
  prompt: string;

  // Slash command invoked (e.g., "analyze")
  command: string | undefined;

  // Variables associated with request (files, selections)
  variables: Record<string, any>;

  // Language model selected by user
  model: LanguageModelChat;

  // Where chat input originated
  location: ChatLocation; // 'chat' | 'quick-chat' | 'inline'
}
```

### 4.3 ChatContext Object

```typescript
interface ChatContext {
  // Message history (filtered to this participant)
  history: Array<ChatRequestTurn | ChatResponseTurn>;
}

interface ChatRequestTurn {
  prompt: string;
  participant: string;
  command: string | undefined;
}

interface ChatResponseTurn {
  response: ChatResponse;
  result: ChatResult;
  participant: string;
  command: string | undefined;
}
```

### 4.4 ChatResponseStream Methods

```typescript
interface ChatResponseStream {
  // Render CommonMark markdown
  markdown(value: string | MarkdownString): void;

  // Add interactive button
  button(options: {
    command: string;
    title: string;
    arguments?: any[];
  }): void;

  // Display file tree preview
  filetree(tree: ChatResponseFileTree[]): void;

  // Show progress status
  progress(message: string): void;

  // Add external reference
  reference(value: Uri | Location): void;

  // Inline URI anchor
  anchor(value: Uri, title?: string): void;

  // Report warning
  warning(message: string): void;

  // Push response part
  push(part: ChatResponsePart): void;
}
```

### 4.5 Handler Implementation Pattern

```typescript
export function activate(context: vscode.ExtensionContext) {
  const participant = vscode.chat.createChatParticipant(
    'extension.myParticipant',
    async (
      request: vscode.ChatRequest,
      context: vscode.ChatContext,
      stream: vscode.ChatResponseStream,
      token: vscode.CancellationToken
    ): Promise<vscode.ChatResult> => {

      // 1. Determine intent from command or prompt
      if (request.command === 'analyze') {
        return handleAnalyze(request, context, stream, token);
      }

      // 2. Access conversation history
      const previousMessages = context.history
        .filter(turn => turn instanceof vscode.ChatRequestTurn)
        .map(turn => turn.prompt);

      // 3. Stream response progressively
      stream.progress('Analyzing your request...');

      // 4. Use language model
      const messages = [
        vscode.LanguageModelChatMessage.User(request.prompt)
      ];
      const response = await request.model.sendRequest(
        messages,
        {},
        token
      );

      // 5. Stream model output
      for await (const fragment of response.text) {
        stream.markdown(fragment);
      }

      // 6. Add interactive elements
      stream.button({
        command: 'extension.applyChanges',
        title: 'Apply Changes',
        arguments: [/* ... */]
      });

      // 7. Return result metadata
      return {
        metadata: {
          command: request.command,
          success: true
        }
      };
    }
  );

  // Set icon
  participant.iconPath = vscode.Uri.joinPath(
    context.extensionUri,
    'icon.png'
  );

  // Provide follow-up suggestions
  participant.followupProvider = {
    provideFollowups(result, context, token) {
      return [
        { prompt: 'Show more details', label: 'More Details' },
        { prompt: 'Explain the changes', label: 'Explain' }
      ];
    }
  };

  context.subscriptions.push(participant);
}
```

### 4.6 Disambiguation (Auto-Routing)

When enabled, VS Code automatically routes requests to participants without explicit `@mention`:

```json
"disambiguation": [
  {
    "category": "testing",
    "description": "User wants to write or run tests",
    "examples": [
      "write a test for this",
      "test this function",
      "create unit tests"
    ]
  }
]
```

**Matching Process:**
1. User sends prompt without `@mention`
2. VS Code compares against all disambiguation examples
3. Highest-confidence match receives the request
4. If no strong match, falls back to default Copilot

---

## 5. Language Model Tool API

### 5.1 Tool Registration Schema

```json
{
  "contributes": {
    "languageModelTools": [
      {
        "name": "extension_analyzeComplexity",
        "tags": ["codeAnalysis", "metrics"],
        "toolReferenceName": "complexity",
        "displayName": "Analyze Complexity",
        "modelDescription": "Analyzes cyclomatic complexity of code. Call when user asks about code complexity, maintainability scores, or wants to identify complex functions. Returns complexity score and recommendations.",
        "userDescription": "Analyze code complexity",
        "canBeReferencedInPrompt": true,
        "icon": "$(graph)",
        "when": "editorLangId =~ /typescript|javascript/",
        "inputSchema": {
          "type": "object",
          "properties": {
            "filePath": {
              "type": "string",
              "description": "Absolute path to the file to analyze"
            },
            "threshold": {
              "type": "number",
              "description": "Complexity threshold for warnings (default: 10)",
              "default": 10
            },
            "includeDetails": {
              "type": "boolean",
              "description": "Include per-function breakdown",
              "default": false
            }
          },
          "required": ["filePath"]
        }
      }
    ]
  }
}
```

### 5.2 LanguageModelTool Interface

```typescript
interface LanguageModelTool<T> {
  // Called before invocation for user confirmation
  prepareInvocation?(
    options: LanguageModelToolInvocationPrepareOptions<T>,
    token: CancellationToken
  ): ProviderResult<PreparedToolInvocation>;

  // Called to execute the tool
  invoke(
    options: LanguageModelToolInvocationOptions<T>,
    token: CancellationToken
  ): ProviderResult<LanguageModelToolResult>;
}

interface PreparedToolInvocation {
  // Message shown during invocation
  invocationMessage: string;

  // Optional confirmation dialog
  confirmationMessages?: {
    title: string;
    message: MarkdownString;
  };
}

interface LanguageModelToolResult {
  // Array of response parts
  content: Array<LanguageModelTextPart | LanguageModelPromptTsxPart>;
}
```

### 5.3 Tool Implementation Example

```typescript
interface IComplexityParams {
  filePath: string;
  threshold?: number;
  includeDetails?: boolean;
}

class ComplexityTool implements vscode.LanguageModelTool<IComplexityParams> {

  async prepareInvocation(
    options: vscode.LanguageModelToolInvocationPrepareOptions<IComplexityParams>,
    token: vscode.CancellationToken
  ) {
    const { filePath, threshold = 10 } = options.input;
    const fileName = path.basename(filePath);

    return {
      invocationMessage: `Analyzing complexity of ${fileName}...`,
      confirmationMessages: {
        title: 'Code Complexity Analysis',
        message: new vscode.MarkdownString(
          `Analyze **${fileName}** with threshold ${threshold}?\n\n` +
          `This will scan the file for complexity metrics.`
        )
      }
    };
  }

  async invoke(
    options: vscode.LanguageModelToolInvocationOptions<IComplexityParams>,
    token: vscode.CancellationToken
  ): Promise<vscode.LanguageModelToolResult> {
    const { filePath, threshold = 10, includeDetails = false } = options.input;

    // Validate file exists
    try {
      await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
    } catch {
      return new vscode.LanguageModelToolResult([
        new vscode.LanguageModelTextPart(`Error: File not found: ${filePath}`)
      ]);
    }

    // Perform analysis
    const result = await this.analyzeFile(filePath, threshold, includeDetails);

    // Return structured result
    return new vscode.LanguageModelToolResult([
      new vscode.LanguageModelTextPart(JSON.stringify(result, null, 2))
    ]);
  }

  private async analyzeFile(
    filePath: string,
    threshold: number,
    includeDetails: boolean
  ) {
    // Implementation...
    return {
      overallScore: 8.5,
      functionsAboveThreshold: 3,
      recommendations: [
        "Consider breaking down 'processData' function",
        "Extract nested conditionals in 'validateInput'"
      ]
    };
  }
}

// Registration in activate()
export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.lm.registerTool(
      'extension_analyzeComplexity',
      new ComplexityTool()
    )
  );
}
```

### 5.4 Tool Selection by LLM

The LLM selects tools based on:

1. **`modelDescription`:** Primary guide for when to invoke
2. **`tags`:** Categorical hints for tool grouping
3. **`when` clause:** Contextual availability (e.g., language-specific)
4. **Conversation context:** Inferred from user intent

**Selection Flow:**
```
User Prompt
    │
    ▼
┌───────────────────────────────────────┐
│ LLM receives:                         │
│ - User prompt                         │
│ - Tool definitions (name, modelDesc)  │
│ - Available tools (filtered by 'when')│
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│ LLM determines:                       │
│ - Which tools to call                 │
│ - Parameter values from context       │
│ - Execution order (sequential/parallel│
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│ Copilot invokes tools:                │
│ - prepareInvocation() → confirmation  │
│ - invoke() → execution                │
│ - Results fed back to LLM             │
└───────────────────────────────────────┘
```

### 5.5 Confirmation Flow

```
┌─────────────────┐
│ Tool Selected   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ Confirmation Dialog                          │
│ ┌───────────────────────────────────────┐   │
│ │ [Title from prepareInvocation]        │   │
│ │                                       │   │
│ │ [Message with editable parameters]    │   │
│ │                                       │   │
│ │ [Allow]  [Allow for Session]  [Deny]  │   │
│ └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Allowed    Denied
    │         │
    ▼         ▼
 invoke()  Skip tool
```

**Approval Levels:**
- **Per-invocation:** Default, requires approval each time
- **Per-session:** "Allow for this session"
- **Per-workspace:** Stored in workspace settings
- **Global:** "Always allow" (use with caution)

---

## 6. MCP Server Integration

### 6.1 Transport Types

**Stdio (Local Process):**
```json
{
  "type": "stdio",
  "command": "node",
  "args": ["./mcp-server.js"],
  "cwd": "/path/to/server",
  "env": {
    "DEBUG": "true",
    "API_KEY": "${input:apiKey}"
  }
}
```

**HTTP (Remote Service):**
```json
{
  "type": "http",
  "url": "https://api.example.com/mcp",
  "headers": {
    "Authorization": "Bearer ${input:token}",
    "X-API-Version": "2"
  }
}
```

### 6.2 mcp.json Configuration

```json
{
  "servers": {
    "my-local-server": {
      "type": "stdio",
      "command": "node",
      "args": ["./server.js"],
      "cwd": "${workspaceFolder}/mcp",
      "env": {
        "NODE_ENV": "development",
        "DB_CONNECTION": "${input:dbConnection}"
      },
      "version": "1.0.0",
      "dev": {
        "watch": "src/**/*.ts",
        "debug": {
          "type": "node",
          "port": 9229
        }
      }
    },
    "my-remote-server": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${input:token}"
      },
      "version": "2.1.0"
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "dbConnection",
      "description": "Database connection string",
      "password": true
    },
    {
      "type": "promptString",
      "id": "token",
      "description": "API Bearer Token",
      "password": true
    }
  ]
}
```

### 6.3 Programmatic Registration API

```typescript
export function activate(context: vscode.ExtensionContext) {
  const changeEmitter = new vscode.EventEmitter<void>();

  const provider: vscode.McpServerDefinitionProvider = {
    // Fired when server list changes
    onDidChangeMcpServerDefinitions: changeEmitter.event,

    // Provide server definitions
    provideMcpServerDefinitions: async (): Promise<vscode.McpServerDefinition[]> => {
      return [
        // Local stdio server
        new vscode.McpStdioServerDefinition({
          label: 'my-local-mcp',
          command: 'node',
          args: ['./server.js'],
          cwd: vscode.Uri.file('/path/to/server'),
          env: { DEBUG: 'true' },
          version: '1.0.0'
        }),

        // Remote HTTP server
        new vscode.McpHttpServerDefinition({
          label: 'my-remote-mcp',
          uri: 'https://api.example.com/mcp',
          headers: { 'X-Client': 'vscode' },
          version: '2.0.0'
        })
      ];
    },

    // Resolve before server starts (auth, setup)
    resolveMcpServerDefinition: async (
      server: vscode.McpServerDefinition
    ): Promise<vscode.McpServerDefinition | undefined> => {
      // Opportunity to:
      // - Prompt for credentials
      // - Validate configuration
      // - Return undefined to abort

      if (server.label === 'my-remote-mcp') {
        const token = await promptForToken();
        if (!token) return undefined;

        // Inject authentication
        (server as vscode.McpHttpServerDefinition).headers = {
          ...server.headers,
          'Authorization': `Bearer ${token}`
        };
      }

      return server;
    }
  };

  context.subscriptions.push(
    vscode.lm.registerMcpServerDefinitionProvider('my-provider', provider)
  );
}
```

### 6.4 MCP Tools in Agent Mode

MCP tools integrate seamlessly with agent mode:

1. **Discovery:** VS Code queries MCP servers for tool definitions
2. **Display:** Tools appear in agent mode picker with descriptions
3. **Invocation:** LLM can invoke MCP tools like built-in tools
4. **Parameters:** Editable in confirmation dialog
5. **Results:** Returned to LLM for continued processing

**Tool Namespacing:**
```
# Reference specific tool
tools: ["my-server/search-docs"]

# Reference all tools from server
tools: ["my-server/*"]

# Built-in servers
tools: ["github/*", "playwright/*"]
```

### 6.5 OAuth 2.1 Authentication

**Supported Flows:**

1. **Dynamic Client Registration (DCR):** Preferred, automated client setup
2. **Client Credentials:** Manual Client ID/Secret entry

**Built-in Provider Support:**
- GitHub
- Microsoft Entra

**Required Redirect URLs:**
- `http://127.0.0.1:33418`
- `https://vscode.dev/redirect`

---

## 7. Internal Prompt Engineering

> **Note:** This section is based on community reverse-engineering and analysis (particularly [this Dev.to article](https://dev.to/seiwan-maikuma/a-deep-dive-into-github-copilot-agent-modes-prompt-structure-2i4g)), not official GitHub documentation. The exact internal prompts are proprietary and subject to change. This represents a plausible model based on observable behavior.

### 7.1 Three-Layer System Prompt Structure

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: SYSTEM (Universal Rules)                           │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ TOOL DEFINITIONS                                     │    │
│ │ - read_file: "Read file contents..."                 │    │
│ │ - edit_file: "Edit files. NEVER show changes..."     │    │
│ │ - run_in_terminal: "Execute terminal commands..."    │    │
│ │ - semantic_search: "Find by meaning..."              │    │
│ │ - grep_search: "Quick keyword search..."             │    │
│ │ - get_errors: "Retrieve compile/lint errors..."      │    │
│ │ - fetch_webpage: "Fetch URL content..."              │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ 8-STEP WORKFLOW                                      │    │
│ │ 1. Deeply understand requirements and edge cases     │    │
│ │ 2. Investigate codebase through targeted exploration │    │
│ │ 3. Produce detailed implementation plan with TODOs   │    │
│ │ 4. Implement changes incrementally with context      │    │
│ │ 5. Debug by finding root causes                      │    │
│ │ 6. Test frequently after each modification           │    │
│ │ 7. Iterate until resolution                          │    │
│ │ 8. Verify completion against original intent         │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ BEHAVIORAL DIRECTIVES                                │    │
│ │ - You are an agent—keep going until resolved         │    │
│ │ - Proceed without repeatedly asking                  │    │
│ │ - Use tools to gather information, don't ask user    │    │
│ │ - NEVER show code changes to user, just apply        │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ SAFETY & POLICY CONSTRAINTS                          │    │
│ │ - Do not execute dangerous commands                  │    │
│ │ - Request confirmation for irreversible actions      │    │
│ │ - Stay within workspace boundaries                   │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ OUTPUT FORMATTING                                    │    │
│ │ - Use Markdown for responses                         │    │
│ │ - Structured output for tool calls                   │    │
│ │ - Clear error messages                               │    │
│ └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: ENVIRONMENT CONTEXT                                 │
│                                                              │
│ <context>                                                    │
│   <currentDate>2025-01-23</currentDate>                     │
│   <operatingSystem>darwin</operatingSystem>                 │
│   <shell>zsh</shell>                                        │
│ </context>                                                   │
│                                                              │
│ <workspaceStructure>                                        │
│   I am working in a workspace with the following folders:   │
│   - src/                                                    │
│     - components/                                           │
│     - utils/                                                │
│   - tests/                                                  │
│   - package.json                                            │
│   [abbreviated for large repos]                             │
│ </workspaceStructure>                                       │
│                                                              │
│ <editorContext>                                             │
│   <currentFile>/src/components/Button.tsx</currentFile>     │
│   <selection>lines 25-42</selection>                        │
│   <language>typescript</language>                           │
│ </editorContext>                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: USER REQUEST                                        │
│                                                              │
│ <userRequest>                                               │
│   <prompt>Refactor this component to use hooks</prompt>     │
│   <attachments>                                             │
│     <selection>                                             │
│       [selected code from editor]                           │
│     </selection>                                            │
│   </attachments>                                            │
│ </userRequest>                                              │
│                                                              │
│ <reminderInstructions>                                      │
│   You are an agent - you must keep going until the user's   │
│   query is completely resolved, before ending your turn     │
│   and yielding back to the user.                            │
│                                                              │
│   Proceed without repeatedly asking the user if you can     │
│   act safely.                                               │
│ </reminderInstructions>                                     │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Built-in Tool Definitions

```typescript
const AGENT_TOOLS = {
  read_file: {
    name: "read_file",
    description: "Read file contents. Specify line range for large files. " +
                 "Large files return outline instead of full content.",
    parameters: {
      path: { type: "string", description: "Absolute file path" },
      startLine: { type: "number", description: "Optional start line" },
      endLine: { type: "number", description: "Optional end line" }
    }
  },

  edit_file: {
    name: "edit_file",
    description: "Edit files. Group changes by file. " +
                 "NEVER show changes to user - just call tool.",
    parameters: {
      path: { type: "string" },
      edits: {
        type: "array",
        items: {
          range: { startLine: "number", endLine: "number" },
          newText: "string"
        }
      }
    }
  },

  run_in_terminal: {
    name: "run_in_terminal",
    description: "Execute terminal commands. Requires user approval.",
    parameters: {
      command: { type: "string" }
    }
  },

  semantic_search: {
    name: "semantic_search",
    description: "Find functions/files by meaning, not keywords. " +
                 "Use when you don't know exact location.",
    parameters: {
      query: { type: "string", description: "Semantic search query" }
    }
  },

  grep_search: {
    name: "grep_search",
    description: "Quick keyword/pattern search within files.",
    parameters: {
      pattern: { type: "string" },
      path: { type: "string", description: "Optional path filter" }
    }
  },

  get_errors: {
    name: "get_errors",
    description: "Retrieve compile/lint errors from editor diagnostics.",
    parameters: {}
  },

  fetch_webpage: {
    name: "fetch_webpage",
    description: "Fetch URL content with linked resources.",
    parameters: {
      url: { type: "string" }
    }
  }
};
```

### 7.3 The Agentic Loop

```
┌──────────────────────────────────────────────────────────────┐
│                      AGENTIC LOOP                            │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ RECEIVE PROMPT  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
         ┌─────────│ PLAN            │
         │         │ - Analyze task  │
         │         │ - Identify tools│
         │         │ - Order steps   │
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │ EXECUTE         │
         │         │ - Call tools    │
         │         │ - Edit files    │
         │         │ - Run commands  │
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │ OBSERVE         │
         │         │ - Check errors  │
         │         │ - Read output   │
         │         │ - Verify state  │
         │         └────────┬────────┘
         │                  │
         │         ┌────────┴────────┐
         │         │    SUCCESS?     │
         │         └────────┬────────┘
         │              │       │
         │           NO │       │ YES
         │              │       │
         └──────────────┘       ▼
                       ┌─────────────────┐
                       │ COMPLETE        │
                       │ - Summarize     │
                       │ - Yield to user │
                       └─────────────────┘
```

---

## 8. Handoffs and Delegation

> **Important Limitation:** Handoffs are supported for custom agents in VS Code and the CLI, but the `handoffs` property is **not supported** for the GitHub.com Copilot coding agent. This section applies to IDE-based agents only.

### 8.1 Handoff Configuration

```yaml
---
name: Planning Agent
description: Creates implementation plans
handoffs:
  - label: "Implement Plan"          # Button text
    agent: "agent"                   # Target agent ID
    prompt: |                        # Pre-filled prompt
      Implement the plan outlined above.
      Follow the numbered steps exactly.
    send: false                      # true = auto-submit

  - label: "Review Plan"
    agent: "reviewer"
    prompt: "Review this plan for potential issues."
    send: false

  - label: "Delegate to Cloud"
    agent: "@cloud"                  # Cloud agent
    prompt: "Complete this task and create a PR."
    send: true                       # Auto-submits
---

# Planning Agent Instructions
...
```

### 8.2 Handoff Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ SOURCE AGENT SESSION                                         │
│                                                              │
│ Agent completes task...                                      │
│                                                              │
│ Response:                                                    │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Here is the implementation plan:                        │  │
│ │ 1. Create new API endpoint                              │  │
│ │ 2. Add validation middleware                            │  │
│ │ 3. Write unit tests                                     │  │
│ │                                                         │  │
│ │ [Implement Plan]  [Review Plan]  [Delegate to Cloud]    │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                     User clicks button
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ TARGET AGENT SESSION                                         │
│                                                              │
│ Context transferred:                                         │
│ - Conversation history                                       │
│ - Pre-filled prompt from handoff                             │
│ - Relevant workspace state                                   │
│                                                              │
│ If send: true → Auto-submits prompt                          │
│ If send: false → User can review/edit before sending         │
│                                                              │
│ Original session archived                                     │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Delegation Commands

**From Local to Background:**
```
@cli implement the authentication module based on the plan above
```

**From Background to Cloud:**
```
/delegate complete the API integration tests and fix failing edge cases
```

**The `/delegate` command:**
1. Commits unstaged changes to new branch
2. Pushes branch to remote
3. Assigns task to Copilot coding agent
4. Transfers full context

### 8.4 Cross-Agent Delegation Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                 MULTI-AGENT WORKFLOW                         │
└─────────────────────────────────────────────────────────────┘

   ┌──────────────┐
   │ LOCAL AGENT  │  "Create a plan for authentication"
   │ (Planning)   │
   └──────┬───────┘
          │ handoff: "Implement Plan"
          ▼
   ┌──────────────┐
   │ LOCAL AGENT  │  "Implement the plan step by step"
   │ (Coding)     │
   └──────┬───────┘
          │ handoff: "Run Tests"
          ▼
   ┌──────────────┐
   │ BACKGROUND   │  "Execute test suite in isolation"
   │ AGENT        │  (worktree isolation)
   └──────┬───────┘
          │ /delegate
          ▼
   ┌──────────────┐
   │ CLOUD AGENT  │  "Create PR with all changes"
   │              │  (team review)
   └──────────────┘
```

---

## 9. Security Model

### 9.1 Trust Boundaries

| Boundary | Scope | Protection Mechanism |
|----------|-------|---------------------|
| **Workspace** | File access | Limited to workspace folder |
| **Extension Publisher** | Code execution | Publisher trust verification |
| **MCP Server** | External tools | Explicit trust + confirmation |
| **Network Domain** | URL access | Two-step approval |
| **Terminal Commands** | System access | Pattern-based approval |

### 9.2 Tool Confirmation Levels

```typescript
// VS Code settings for tool confirmation
{
  // Per-tool auto-approval
  "chat.tools.terminal.autoApprove": {
    "allowed": ["npm test", "git status", "ls"],
    "denied": ["rm -rf", "sudo *", "chmod 777"]
  },

  // File edit patterns
  "chat.tools.editFiles.autoApprove": {
    "src/**/*.ts": true,
    "*.config.js": false,
    "node_modules/**": false
  }
}
```

### 9.3 MCP Security

**Server Trust:**
1. User must explicitly trust each MCP server
2. First tool invocation shows detailed confirmation
3. `readOnlyHint` annotation can skip confirmation for safe operations

**Authentication:**
- OAuth 2.1 with PKCE required for sensitive servers
- Secrets never stored in plain text
- Token refresh handled automatically

### 9.4 Workspace Isolation

- Agents cannot access files outside workspace
- Background agents use separate worktrees
- Cloud agents operate in sandboxed environments
- Firewall controls internet access for cloud agents

---

## 10. Comparison to Claude Code/BAZINGA

### 10.1 Architecture Comparison

| Aspect | GitHub Copilot | Claude Code | BAZINGA |
|--------|---------------|-------------|---------|
| **Agent Spawning** | `#runSubagent`, handoffs, `@agent` | `Task()` with explicit prompts | `Task()` with agent templates |
| **Context Isolation** | Subagents get isolated context | Task spawns inherit context | Configurable per-agent |
| **Skills Location** | `.github/skills/`, `~/.copilot/skills/` | `.claude/skills/` | `.claude/skills/` |
| **Skill Format** | SKILL.md + YAML frontmatter | SKILL.md + YAML frontmatter | SKILL.md + YAML frontmatter |
| **Skill Discovery** | Automatic by description | Explicit invocation | Explicit via `Skill()` |
| **Skill Loading** | Progressive (3-level) | Full load on invocation | Full load on invocation |
| **Tool Definition** | package.json + TypeScript | Inline in skill | Inline in skill |
| **MCP Support** | Native via mcp.json | Native via MCP tool | Via Claude Code |
| **State Persistence** | In-memory session | Manual | SQLite database |
| **Multi-Agent Orchestration** | Handoffs (user-driven) | Flat Task() calls | Dedicated orchestrator |

### 10.2 Key Differences

#### Skill Activation
**Copilot:** Automatic based on prompt matching to skill descriptions
**BAZINGA:** Explicit via `Skill(command: "skill-name")`

**Implication:** Copilot's approach requires less user knowledge but may activate wrong skills. BAZINGA's explicit approach is more predictable but requires knowing skill names.

#### Agent Communication
**Copilot:** Handoffs with context transfer, user-driven progression
**BAZINGA:** Orchestrator routes between agents, automated workflow

**Implication:** Copilot gives users more control; BAZINGA is more autonomous.

#### Context Management
**Copilot:** Isolated subagent contexts, auto-compaction at 95%
**BAZINGA:** Inherited context, manual management

**Implication:** Copilot better handles long tasks; BAZINGA risks context overflow.

### 10.3 What Copilot Does Well

1. **Progressive skill loading** reduces context consumption
2. **Automatic skill activation** based on semantic matching
3. **Handoff buttons** provide clean agent transitions
4. **Worktree isolation** prevents workspace conflicts
5. **Unified tool aliases** (`read`, `edit`, `search`) simplify configuration
6. **MCP integration** standardizes external tool access
7. **OAuth 2.1 support** enables secure authentication

### 10.4 What BAZINGA Does Better (UPDATED Jan 2026)

1. **Explicit orchestration** with dedicated coordinator agent (Copilot now has `#runSubagent`)
2. **Database-backed state** for persistent session tracking (Copilot sessions ephemeral without skill)
3. ~~**Multi-agent parallelism**~~ - Copilot now supports parallel execution (PR #2839, Jan 15, 2026)
4. **Quality gates** (QA → Tech Lead → PM) ensure code quality (can be replicated in Copilot agents)
5. **Specialization system** with version-aware templates (unique to BAZINGA)
6. **Token budgeting** per-model limits (unique to BAZINGA)
7. **Success criteria tracking** with verification (unique to BAZINGA)
8. **Per-agent model selection** (haiku/sonnet/opus) - Copilot uses single model

### 10.5 Potential Improvements for BAZINGA

| Feature | Copilot Implementation | BAZINGA Adoption |
|---------|----------------------|------------------|
| Progressive skill loading | 3-level system | Implement Level 1/2 separation |
| Automatic skill selection | Semantic matching | Add description-based matching |
| Subagent context isolation | Separate context windows | Configurable context inheritance |
| Worktree isolation | Git worktree per agent | Optional worktree mode |
| Handoff buttons | YAML-configured transitions | Dashboard workflow buttons |
| Unified tool aliases | Case-insensitive aliases | Standardize tool names |
| Auto-compaction | 95% trigger | Implement conversation summarization |

---

## 11. Critical Analysis

### 11.1 Pros

#### Architecture
- **Clean separation of concerns** across four agent tiers
- **Progressive loading** minimizes context usage
- **MCP standardization** enables ecosystem growth
- **Worktree isolation** prevents workspace corruption

#### Developer Experience
- **Automatic skill activation** requires no learning curve
- **Handoffs** create guided workflows
- **Unified management** in Chat view
- **Cross-platform portability** (skills work across agents)

#### Extensibility
- **Chat Participant API** enables rich extensions
- **Language Model Tool API** for custom tools
- **MCP servers** for external integrations
- **OAuth 2.1** for secure authentication

### 11.2 Cons

#### Complexity
- **Four agent types** with different capabilities create confusion
- **Multiple skill locations** (`.github/`, `.claude/`, `~/`) fragment discovery
- **Tool confirmation fatigue** from excessive prompts
- **MCP configuration** requires server setup

#### Limitations
- **No subagent nesting** limits complex workflows
- **Background agents can't use MCP** severely limits their utility
- **Cloud agents lack editor context** (no test results, selections)
- **64k token limit** (128k in Insiders only)

#### ~~Gaps~~ Remaining Differences vs. BAZINGA (UPDATED Jan 2026)
- ~~**No dedicated orchestrator**~~ - `#runSubagent` enables autonomous orchestration
- **No database state** - sessions are ephemeral (but bazinga-db skill works on Copilot)
- **No quality gates** - no enforced review workflow (but can encode in agent prompts)
- ~~**No parallelism**~~ - **RESOLVED** (PR #2839 merged Jan 15, 2026)
- **No specialization system** - generic prompts only (BAZINGA advantage)
- **No per-agent model selection** - single model for all agents (BAZINGA advantage)

### 11.3 Verdict (UPDATED Jan 2026)

**GitHub Copilot has achieved near-feature parity with Claude Code for multi-agent orchestration.**

With `#runSubagent` (programmatic spawning) and parallel execution (PR #2839), Copilot can now:
- ✅ Spawn agents autonomously
- ✅ Run multiple agents in parallel
- ✅ Chain complex workflows

**BAZINGA's remaining unique advantages:**
- Per-agent model selection (haiku/sonnet/opus)
- Specialization system with version-aware templates
- Token budgeting per-model
- Database-backed state (via bazinga-db skill)

BAZINGA could still benefit from adopting:
- Progressive skill loading
- Automatic skill selection
- Context isolation options
- Worktree integration
- Unified tool aliases

---

## 12. Implementation Recommendations

### 12.1 Immediate Adoptions (Low Effort, High Value)

#### 1. Progressive Skill Loading
Implement 3-level loading for BAZINGA skills:

```python
class SkillLoader:
    def __init__(self):
        self.registry = {}  # Level 1: name + description only

    def discover(self, skills_dir: str):
        """Level 1: Read YAML frontmatter only"""
        for skill_path in glob(f"{skills_dir}/*/SKILL.md"):
            frontmatter = self.parse_frontmatter(skill_path)
            self.registry[frontmatter['name']] = {
                'description': frontmatter['description'],
                'path': skill_path
            }

    def load_instructions(self, skill_name: str) -> str:
        """Level 2: Load SKILL.md body"""
        path = self.registry[skill_name]['path']
        return self.parse_body(path)

    def load_resource(self, skill_name: str, resource_path: str) -> str:
        """Level 3: Load supporting file"""
        base = os.path.dirname(self.registry[skill_name]['path'])
        return self.read_file(os.path.join(base, resource_path))
```

#### 2. Unified Tool Aliases
Add alias support to skill/tool invocation:

```python
TOOL_ALIASES = {
    'execute': ['shell', 'bash', 'powershell', 'terminal'],
    'read': ['Read', 'view', 'cat'],
    'edit': ['Edit', 'Write', 'modify'],
    'search': ['Grep', 'Glob', 'find'],
}

def resolve_tool(name: str) -> str:
    name_lower = name.lower()
    for canonical, aliases in TOOL_ALIASES.items():
        if name_lower == canonical or name_lower in [a.lower() for a in aliases]:
            return canonical
    return name
```

#### 3. Skill Description Matching
Add automatic skill selection:

```python
def match_skills(prompt: str, skill_registry: dict) -> list[str]:
    """Match prompt against skill descriptions using semantic similarity"""
    matches = []
    for name, info in skill_registry.items():
        similarity = compute_similarity(prompt, info['description'])
        if similarity > 0.7:  # Threshold
            matches.append((name, similarity))
    return sorted(matches, key=lambda x: x[1], reverse=True)
```

### 12.2 Medium-Term Adoptions (Medium Effort)

#### 1. Context Isolation Option
Allow agents to run in isolated context:

```yaml
# In agent template
context_mode: isolated  # or 'inherited' (default)
context_budget: 32000   # Token limit for this agent
```

#### 2. Handoff Buttons in Dashboard
Add workflow buttons to session detail view:

```typescript
interface HandoffConfig {
  label: string;
  targetAgent: AgentType;
  prompt: string;
  autoSubmit: boolean;
}

// Example in dashboard
const handoffs: HandoffConfig[] = [
  { label: "Send to QA", targetAgent: "qa_expert", prompt: "Test this implementation", autoSubmit: false },
  { label: "Send to Tech Lead", targetAgent: "tech_lead", prompt: "Review for approval", autoSubmit: false },
];
```

#### 3. Auto-Compaction
Implement conversation summarization:

```python
def check_context_usage(context: SessionContext) -> float:
    """Returns percentage of context used"""
    return context.token_count / context.max_tokens

def compact_if_needed(context: SessionContext):
    if check_context_usage(context) > 0.95:
        summary = summarize_conversation(context.history)
        context.history = [summary]
        log_compaction(context.session_id)
```

### 12.3 Long-Term Considerations

#### 1. MCP Server Support
Consider adding MCP server definitions for BAZINGA tools:

```json
{
  "servers": {
    "bazinga-db": {
      "type": "stdio",
      "command": "python",
      "args": [".claude/skills/bazinga-db/scripts/bazinga_db.py", "--mcp-mode"]
    }
  }
}
```

#### 2. Worktree Isolation Mode
For complex refactoring tasks, offer worktree isolation:

```python
class WorktreeAgent:
    def __init__(self, session_id: str):
        self.worktree_path = self.create_worktree(session_id)

    def create_worktree(self, session_id: str) -> str:
        path = f".git/worktrees/bazinga-{session_id}"
        subprocess.run(["git", "worktree", "add", path, "-b", f"bazinga/{session_id}"])
        return path

    def apply_changes(self):
        """Merge worktree changes to main workspace"""
        subprocess.run(["git", "merge", f"bazinga/{self.session_id}"])
        self.cleanup()
```

---

## Sources

### Official Documentation
- [VS Code Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [VS Code Chat Participant API](https://code.visualstudio.com/api/extension-guides/ai/chat)
- [VS Code Language Model Tool API](https://code.visualstudio.com/api/extension-guides/ai/tools)
- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [VS Code Agents Overview](https://code.visualstudio.com/docs/copilot/agents/overview)
- [VS Code Background Agents](https://code.visualstudio.com/docs/copilot/agents/background-agents)
- [VS Code Custom Agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [GitHub Docs - About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [GitHub Docs - Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

### GitHub Blog and Changelog
- [GitHub Copilot Now Supports Agent Skills](https://github.blog/changelog/2025-12-18-github-copilot-now-supports-agent-skills/)
- [Agent Mode 101](https://github.blog/ai-and-ml/github-copilot/agent-mode-101-all-about-github-copilots-powerful-mode/)
- [Custom Agents for GitHub Copilot](https://github.blog/changelog/2025-10-28-custom-agents-for-github-copilot/)
- [CLI Custom Agents and Delegation](https://github.blog/changelog/2025-10-28-github-copilot-cli-use-custom-agents-and-delegate-to-copilot-coding-agent/)

### Technical Analysis
- [Deep Dive into Agent Mode Prompt Structure](https://dev.to/seiwan-maikuma/a-deep-dive-into-github-copilot-agent-modes-prompt-structure-2i4g)
- [Mastering Subagents in VS Code](https://imaginet.com/2025/mastering-subagents-in-vs-code-copilot-how-to-actually-use-them/)

---

## Multi-LLM Review Integration

**Status:** Completed via three-way debate (Gemini + Claude + Web Sources)
**Date:** 2025-01-23

### Consensus Points (All Agreed)

1. **Chat Participant API (Section 4):** Accurately describes the public VS Code API
2. **Language Model Tool API (Section 5):** Correctly documents tool registration and interfaces
3. **MCP Integration (Section 6):** Accurately reflects publicly documented MCP support
4. **Handoffs (Section 8):** Correctly describes handoff configuration for IDE agents

### Incorporated Feedback

1. **Section 7 (Internal Prompt):** Added disclaimer that this section is based on community reverse-engineering, not official documentation
2. **Section 8 (Handoffs):** Added note that handoffs are IDE-only, not supported for GitHub.com coding agent
3. **Section 2.4 (Token Limits):** Added caveat that exact limits may vary by model

### Rejected Suggestions (With Reasoning)

1. **Gemini suggested:** "Four-tier hierarchy is not officially documented"
   - **Rejected because:** VS Code documentation at [code.visualstudio.com/docs/copilot/agents/overview](https://code.visualstudio.com/docs/copilot/agents/overview) explicitly documents Local, Background, Cloud, and Third-party agents

2. **Gemini suggested:** "`#runSubagent` is not a documented public feature"
   - **Rejected because:** Multiple VS Code GitHub issues ([#275855](https://github.com/microsoft/vscode/issues/275855), [#274630](https://github.com/microsoft/vscode/issues/274630)) confirm `#runSubagent` exists

3. **Gemini suggested:** "SKILL.md is not a documented Copilot feature"
   - **Rejected because:** GitHub Changelog [December 18, 2025](https://github.blog/changelog/2025-12-18-github-copilot-now-supports-agent-skills/) officially announced Agent Skills with SKILL.md format

### Verification Summary

| Section | Verdict | Notes |
|---------|---------|-------|
| 1. Agent Architecture | ✅ VERIFIED | Four types documented in VS Code |
| 2. Sub-Agent System | ✅ VERIFIED | `#runSubagent` confirmed via GitHub issues |
| 3. Skills System | ✅ VERIFIED | Announced Dec 2025, matches description |
| 4. Chat Participant API | ✅ VERIFIED | Matches VS Code API reference |
| 5. Language Model Tool API | ✅ VERIFIED | Matches VS Code API reference |
| 6. MCP Integration | ✅ VERIFIED | Publicly documented |
| 7. Internal Prompt | ⚠️ UNVERIFIED | Based on community analysis (disclaimer added) |
| 8. Handoffs | ✅ VERIFIED | IDE-only limitation noted |
