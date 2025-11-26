"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  Settings2,
  Bot,
  Wand2,
  FileJson,
  Save,
  RotateCcw,
  Check,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Info,
} from "lucide-react";

interface ModelConfig {
  agent_role: string;
  model: string;
  rationale: string;
}

interface ProjectContextEditorProps {
  sessionId?: string;
}

// Model tiers with descriptions
const MODEL_INFO: Record<string, { color: string; description: string }> = {
  haiku: { color: "green", description: "Fast & cost-efficient" },
  sonnet: { color: "purple", description: "Balanced performance" },
  opus: { color: "orange", description: "Maximum capability" },
};

// Default model configs based on schema
const DEFAULT_MODEL_CONFIG: ModelConfig[] = [
  { agent_role: "developer", model: "haiku", rationale: "Cost-efficient for L1-2 tasks" },
  { agent_role: "senior_software_engineer", model: "sonnet", rationale: "Complex failures and L3+ tasks" },
  { agent_role: "qa_expert", model: "sonnet", rationale: "Test generation and validation" },
  { agent_role: "tech_lead", model: "opus", rationale: "Architectural decisions - non-negotiable" },
  { agent_role: "project_manager", model: "opus", rationale: "Strategic planning - non-negotiable" },
  { agent_role: "investigator", model: "opus", rationale: "Root cause analysis" },
  { agent_role: "validator", model: "sonnet", rationale: "BAZINGA verification" },
];

function ModelConfigEditor({
  config,
  onChange,
}: {
  config: ModelConfig[];
  onChange: (updated: ModelConfig[]) => void;
}) {
  const [expandedRoles, setExpandedRoles] = useState<Set<string>>(new Set());

  const toggleRole = (role: string) => {
    const newExpanded = new Set(expandedRoles);
    if (newExpanded.has(role)) {
      newExpanded.delete(role);
    } else {
      newExpanded.add(role);
    }
    setExpandedRoles(newExpanded);
  };

  const updateModel = (role: string, newModel: string) => {
    onChange(
      config.map((c) => (c.agent_role === role ? { ...c, model: newModel } : c))
    );
  };

  const updateRationale = (role: string, newRationale: string) => {
    onChange(
      config.map((c) => (c.agent_role === role ? { ...c, rationale: newRationale } : c))
    );
  };

  return (
    <div className="space-y-2">
      {config.map((item) => {
        const isExpanded = expandedRoles.has(item.agent_role);
        const modelInfo = MODEL_INFO[item.model];
        const isLocked = ["tech_lead", "project_manager"].includes(item.agent_role);

        return (
          <div key={item.agent_role} className="rounded-lg border">
            <div
              className="flex items-center justify-between p-3 cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => toggleRole(item.agent_role)}
            >
              <div className="flex items-center gap-3">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
                <Bot className="h-4 w-4" />
                <span className="font-medium capitalize">
                  {item.agent_role.replace(/_/g, " ")}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {isLocked && (
                  <Badge variant="outline" className="text-xs">
                    Locked
                  </Badge>
                )}
                <Badge
                  variant="secondary"
                  className={cn(
                    modelInfo?.color === "green" && "bg-green-500/20 text-green-500",
                    modelInfo?.color === "purple" && "bg-purple-500/20 text-purple-500",
                    modelInfo?.color === "orange" && "bg-orange-500/20 text-orange-500"
                  )}
                >
                  {item.model}
                </Badge>
              </div>
            </div>

            {isExpanded && (
              <div className="p-3 pt-0 space-y-3">
                <Separator />
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(MODEL_INFO).map(([model, info]) => (
                    <Button
                      key={model}
                      variant={item.model === model ? "default" : "outline"}
                      size="sm"
                      disabled={isLocked && model !== item.model}
                      onClick={(e) => {
                        e.stopPropagation();
                        updateModel(item.agent_role, model);
                      }}
                      className="w-full justify-start"
                    >
                      <span className="capitalize">{model}</span>
                    </Button>
                  ))}
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Rationale</label>
                  <Textarea
                    value={item.rationale}
                    onChange={(e) => updateRationale(item.agent_role, e.target.value)}
                    placeholder="Explain model choice..."
                    className="mt-1 h-16 text-sm resize-none"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                {isLocked && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 rounded-md p-2">
                    <Info className="h-3 w-3" />
                    This role requires maximum capability and cannot be downgraded
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function RawJsonEditor({
  value,
  onChange,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  const [error, setError] = useState<string | null>(null);

  const handleChange = (newValue: string) => {
    onChange(newValue);
    try {
      JSON.parse(newValue);
      setError(null);
    } catch (e) {
      setError("Invalid JSON");
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">{label}</label>
        {error && (
          <span className="text-xs text-red-500 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {error}
          </span>
        )}
      </div>
      <Textarea
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        className={cn(
          "font-mono text-sm min-h-[200px]",
          error && "border-red-500 focus-visible:ring-red-500"
        )}
        placeholder="{}"
      />
    </div>
  );
}

export function ProjectContextEditor({ sessionId }: ProjectContextEditorProps) {
  const [modelConfig, setModelConfig] = useState<ModelConfig[]>(DEFAULT_MODEL_CONFIG);
  const [skillsConfig, setSkillsConfig] = useState("{}");
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<"models" | "skills" | "raw">("models");

  // Load config from localStorage
  useEffect(() => {
    const storedModels = localStorage.getItem("bazinga-model-config");
    const storedSkills = localStorage.getItem("bazinga-skills-config");

    if (storedModels) {
      try {
        setModelConfig(JSON.parse(storedModels));
      } catch {
        // Use defaults
      }
    }
    if (storedSkills) {
      setSkillsConfig(storedSkills);
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem("bazinga-model-config", JSON.stringify(modelConfig));
    localStorage.setItem("bazinga-skills-config", skillsConfig);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setModelConfig(DEFAULT_MODEL_CONFIG);
    setSkillsConfig("{}");
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Project Configuration
          </CardTitle>
          <CardDescription>
            Configure model assignments and skill settings for BAZINGA orchestration
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Tab Navigation */}
          <div className="flex gap-2 mb-4">
            <Button
              variant={activeTab === "models" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("models")}
            >
              <Bot className="h-4 w-4 mr-2" />
              Models
            </Button>
            <Button
              variant={activeTab === "skills" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("skills")}
            >
              <Wand2 className="h-4 w-4 mr-2" />
              Skills
            </Button>
            <Button
              variant={activeTab === "raw" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("raw")}
            >
              <FileJson className="h-4 w-4 mr-2" />
              Raw JSON
            </Button>
          </div>

          {/* Tab Content */}
          {activeTab === "models" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Assign AI models to agent roles. Higher-tier models offer better reasoning
                but cost more tokens.
              </p>
              <ModelConfigEditor config={modelConfig} onChange={setModelConfig} />
            </div>
          )}

          {activeTab === "skills" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Configure which skills are enabled and their settings.
              </p>
              <div className="rounded-lg border p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-red-500/20 text-red-500">
                      security-scan
                    </Badge>
                    <span className="text-sm">Security vulnerability detection</span>
                  </div>
                  <Badge variant="outline">Enabled</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-green-500/20 text-green-500">
                      test-coverage
                    </Badge>
                    <span className="text-sm">Test coverage analysis</span>
                  </div>
                  <Badge variant="outline">Enabled</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-yellow-500/20 text-yellow-500">
                      lint-check
                    </Badge>
                    <span className="text-sm">Code style and quality</span>
                  </div>
                  <Badge variant="outline">Enabled</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-blue-500/20 text-blue-500">
                      codebase-analysis
                    </Badge>
                    <span className="text-sm">Pattern and structure analysis</span>
                  </div>
                  <Badge variant="outline">Enabled</Badge>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Skills are automatically invoked by agents during orchestration.
                Use Raw JSON tab for advanced configuration.
              </p>
            </div>
          )}

          {activeTab === "raw" && (
            <div className="space-y-4">
              <RawJsonEditor
                label="Model Configuration"
                value={JSON.stringify(modelConfig, null, 2)}
                onChange={(v) => {
                  try {
                    setModelConfig(JSON.parse(v));
                  } catch {
                    // Keep existing
                  }
                }}
              />
              <RawJsonEditor
                label="Skills Configuration"
                value={skillsConfig}
                onChange={setSkillsConfig}
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={handleReset}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
            <Button onClick={handleSave}>
              {saved ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Saved
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Configuration Notes</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Model assignments affect token usage and response quality</li>
                <li>Tech Lead and Project Manager roles are locked to Opus for reliability</li>
                <li>Changes are saved to browser storage and persist across sessions</li>
                <li>For production use, these settings should be synced to the database</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
