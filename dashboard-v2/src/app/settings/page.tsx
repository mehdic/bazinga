"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "next-themes";
import { useSocketStore } from "@/lib/socket/client";
import {
  Settings,
  Moon,
  Sun,
  Monitor,
  Database,
  Bell,
  Palette,
  Info,
  Zap,
  Wifi,
  WifiOff,
  Check,
  X,
  AlertTriangle,
  Volume2,
  VolumeX,
} from "lucide-react";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { isConnected } = useSocketStore();
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>("default");
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [bazingaAlerts, setBazingaAlerts] = useState(true);
  const [sessionAlerts, setSessionAlerts] = useState(true);
  const [errorAlerts, setErrorAlerts] = useState(true);

  // Check notification permission on mount
  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  // Load settings from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("bazinga-notification-settings");
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          setSoundEnabled(settings.soundEnabled ?? true);
          setBazingaAlerts(settings.bazingaAlerts ?? true);
          setSessionAlerts(settings.sessionAlerts ?? true);
          setErrorAlerts(settings.errorAlerts ?? true);
        } catch (e) {
          // Ignore parse errors
        }
      }
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = (newSettings: Partial<{
    soundEnabled: boolean;
    bazingaAlerts: boolean;
    sessionAlerts: boolean;
    errorAlerts: boolean;
  }>) => {
    const current = {
      soundEnabled,
      bazingaAlerts,
      sessionAlerts,
      errorAlerts,
      ...newSettings,
    };
    localStorage.setItem("bazinga-notification-settings", JSON.stringify(current));
  };

  const requestNotificationPermission = async () => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);

      if (permission === "granted") {
        // Show test notification
        new Notification("BAZINGA Dashboard", {
          body: "Notifications enabled! You'll be notified when sessions complete.",
          icon: "/favicon.ico",
        });
      }
    } catch (error) {
      console.error("Error requesting notification permission:", error);
    }
  };

  const testNotification = () => {
    if (notificationPermission === "granted") {
      new Notification("Test Notification", {
        body: "This is a test notification from BAZINGA Dashboard",
        icon: "/favicon.ico",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings className="h-6 w-6" />
          Settings
        </h1>
        <p className="text-muted-foreground">
          Configure your dashboard preferences
        </p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Appearance
          </CardTitle>
          <CardDescription>Customize the look and feel of the dashboard</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Theme</label>
            <div className="flex gap-2">
              <Button
                variant={theme === "light" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("light")}
              >
                <Sun className="h-4 w-4 mr-2" />
                Light
              </Button>
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("dark")}
              >
                <Moon className="h-4 w-4 mr-2" />
                Dark
              </Button>
              <Button
                variant={theme === "system" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("system")}
              >
                <Monitor className="h-4 w-4 mr-2" />
                System
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          <CardDescription>Configure notification preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Browser Notifications Permission */}
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Browser Notifications</p>
              <p className="text-sm text-muted-foreground">
                Get notified when sessions complete
              </p>
            </div>
            <div className="flex items-center gap-2">
              {notificationPermission === "granted" ? (
                <>
                  <Badge variant="secondary" className="bg-green-500/20 text-green-500 gap-1">
                    <Check className="h-3 w-3" />
                    Enabled
                  </Badge>
                  <Button variant="outline" size="sm" onClick={testNotification}>
                    Test
                  </Button>
                </>
              ) : notificationPermission === "denied" ? (
                <Badge variant="destructive" className="gap-1">
                  <X className="h-3 w-3" />
                  Blocked
                </Badge>
              ) : (
                <Button variant="outline" size="sm" onClick={requestNotificationPermission}>
                  Enable
                </Button>
              )}
            </div>
          </div>

          {notificationPermission === "denied" && (
            <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3 text-sm">
              <div className="flex items-center gap-2 text-yellow-500">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">Notifications blocked</span>
              </div>
              <p className="mt-1 text-muted-foreground">
                Please enable notifications in your browser settings to receive alerts.
              </p>
            </div>
          )}

          <Separator />

          {/* Notification Types */}
          <div className="space-y-3">
            <p className="text-sm font-medium">Notification Types</p>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">BAZINGA Completion</p>
                <p className="text-xs text-muted-foreground">
                  Alert when a session completes successfully
                </p>
              </div>
              <Switch
                checked={bazingaAlerts}
                onCheckedChange={(checked) => {
                  setBazingaAlerts(checked);
                  saveSettings({ bazingaAlerts: checked });
                }}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Session Started</p>
                <p className="text-xs text-muted-foreground">
                  Alert when a new session begins
                </p>
              </div>
              <Switch
                checked={sessionAlerts}
                onCheckedChange={(checked) => {
                  setSessionAlerts(checked);
                  saveSettings({ sessionAlerts: checked });
                }}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Errors & Blocks</p>
                <p className="text-xs text-muted-foreground">
                  Alert when agents are blocked or fail
                </p>
              </div>
              <Switch
                checked={errorAlerts}
                onCheckedChange={(checked) => {
                  setErrorAlerts(checked);
                  saveSettings({ errorAlerts: checked });
                }}
              />
            </div>
          </div>

          <Separator />

          {/* Sound */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {soundEnabled ? (
                <Volume2 className="h-4 w-4 text-muted-foreground" />
              ) : (
                <VolumeX className="h-4 w-4 text-muted-foreground" />
              )}
              <div>
                <p className="font-medium">Notification Sound</p>
                <p className="text-sm text-muted-foreground">
                  Play sound with notifications
                </p>
              </div>
            </div>
            <Switch
              checked={soundEnabled}
              onCheckedChange={(checked) => {
                setSoundEnabled(checked);
                saveSettings({ soundEnabled: checked });
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Connection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="h-5 w-5 text-green-500" />
            ) : (
              <WifiOff className="h-5 w-5 text-muted-foreground" />
            )}
            Real-time Connection
          </CardTitle>
          <CardDescription>WebSocket connection status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Status</p>
              <p className="text-sm text-muted-foreground">
                Socket.io real-time updates
              </p>
            </div>
            <Badge
              variant={isConnected ? "secondary" : "outline"}
              className={isConnected ? "bg-green-500/20 text-green-500" : ""}
            >
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-refresh</p>
              <p className="text-sm text-muted-foreground">
                Fallback polling every 10 seconds
              </p>
            </div>
            <Badge variant="secondary">Enabled</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Database */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Database
          </CardTitle>
          <CardDescription>Database connection and status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Connection Status</p>
              <p className="text-sm text-muted-foreground">SQLite database (read-only)</p>
            </div>
            <Badge variant="secondary" className="bg-green-500/20 text-green-500">
              Connected
            </Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Database Path</p>
              <p className="text-sm text-muted-foreground font-mono">
                ../bazinga/bazinga.db
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            About
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              <span className="font-bold">BAZINGA Dashboard</span>
            </div>
            <Badge>v2.0.0</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Real-time orchestration monitoring and analytics dashboard for the BAZINGA
            multi-agent development system.
          </p>
          <Separator />
          <div className="text-xs text-muted-foreground space-y-1">
            <p>Built with Next.js 14, TypeScript, Tailwind CSS, and shadcn/ui</p>
            <p>Database: SQLite with Drizzle ORM</p>
            <p>API: tRPC with TanStack Query</p>
            <p>Real-time: Socket.io with Zustand</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
