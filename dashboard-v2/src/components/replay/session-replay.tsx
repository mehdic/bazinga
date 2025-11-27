"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, AGENT_COLORS_TW } from "@/lib/utils";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
  RotateCcw,
  Clock,
  User,
  Code,
  TestTube,
  GitPullRequest,
  Bot,
} from "lucide-react";

// Log entry matching actual database schema
interface LogEntry {
  id: number;
  agentType: string;
  content: string;
  timestamp: string | null;
  iteration: number | null;
  agentId: string | null;
}

interface SessionReplayProps {
  logs: LogEntry[];
  sessionStatus: string | null;
}

const AGENT_ICONS: Record<string, React.ElementType> = {
  pm: User,
  developer: Code,
  qa_expert: TestTube,
  tech_lead: GitPullRequest,
  orchestrator: Bot,
  investigator: Bot,
};

const PLAYBACK_SPEEDS = [0.5, 1, 2, 4];

export function SessionReplay({ logs, sessionStatus }: SessionReplayProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // Sort logs chronologically
  const sortedLogs = useMemo(() => {
    return [...logs].sort(
      (a, b) => {
        const aTime = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const bTime = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return aTime - bTime;
      }
    );
  }, [logs]);

  const currentLog = sortedLogs[currentIndex];
  const progress = sortedLogs.length > 0 ? ((currentIndex + 1) / sortedLogs.length) * 100 : 0;

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying || currentIndex >= sortedLogs.length - 1) {
      if (currentIndex >= sortedLogs.length - 1) {
        setIsPlaying(false);
      }
      return;
    }

    const interval = setInterval(() => {
      setCurrentIndex((prev) => Math.min(prev + 1, sortedLogs.length - 1));
    }, 2000 / playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, currentIndex, sortedLogs.length, playbackSpeed]);

  const handlePlayPause = useCallback(() => {
    if (currentIndex >= sortedLogs.length - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying((prev) => !prev);
  }, [currentIndex, sortedLogs.length]);

  const handlePrevious = useCallback(() => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
    setIsPlaying(false);
  }, []);

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) => Math.min(prev + 1, sortedLogs.length - 1));
    setIsPlaying(false);
  }, [sortedLogs.length]);

  const handleReset = useCallback(() => {
    setCurrentIndex(0);
    setIsPlaying(false);
  }, []);

  const handleSkipBack = useCallback(() => {
    setCurrentIndex((prev) => Math.max(prev - 5, 0));
    setIsPlaying(false);
  }, []);

  const handleSkipForward = useCallback(() => {
    setCurrentIndex((prev) => Math.min(prev + 5, sortedLogs.length - 1));
    setIsPlaying(false);
  }, [sortedLogs.length]);

  const cycleSpeed = useCallback(() => {
    setPlaybackSpeed((prev) => {
      const currentIdx = PLAYBACK_SPEEDS.indexOf(prev);
      return PLAYBACK_SPEEDS[(currentIdx + 1) % PLAYBACK_SPEEDS.length];
    });
  }, []);

  // Get elapsed time from start
  const getElapsedTime = (log: LogEntry) => {
    if (sortedLogs.length === 0 || !log.timestamp || !sortedLogs[0].timestamp) return "0:00";
    const start = new Date(sortedLogs[0].timestamp).getTime();
    const current = new Date(log.timestamp).getTime();
    const diffMs = current - start;
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  if (sortedLogs.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Play className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No logs available for replay</p>
        </CardContent>
      </Card>
    );
  }

  const CurrentIcon = currentLog ? AGENT_ICONS[currentLog.agentType] || Bot : Bot;

  return (
    <div className="space-y-4">
      {/* Timeline Progress */}
      <Card>
        <CardContent className="p-4">
          <div className="space-y-3">
            {/* Progress Bar */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground w-12">
                {currentIndex + 1}/{sortedLogs.length}
              </span>
              <Progress value={progress} className="flex-1 h-2" />
              <span className="text-sm text-muted-foreground w-12 text-right">
                {currentLog ? getElapsedTime(currentLog) : "0:00"}
              </span>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center justify-center gap-2">
              <Button variant="ghost" size="icon" onClick={handleReset}>
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleSkipBack}>
                <Rewind className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handlePrevious}>
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button
                variant="default"
                size="icon"
                className="h-10 w-10"
                onClick={handlePlayPause}
              >
                {isPlaying ? (
                  <Pause className="h-5 w-5" />
                ) : (
                  <Play className="h-5 w-5" />
                )}
              </Button>
              <Button variant="ghost" size="icon" onClick={handleNext}>
                <SkipForward className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleSkipForward}>
                <FastForward className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={cycleSpeed}>
                {playbackSpeed}x
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Step Display */}
      {currentLog && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    AGENT_COLORS_TW[currentLog.agentType] || "bg-gray-500"
                  )}
                >
                  <CurrentIcon className="h-4 w-4 text-white" />
                </div>
                <span className="capitalize">
                  {currentLog.agentType.replace("_", " ")}
                </span>
              </CardTitle>
              <div className="flex items-center gap-2">
                {currentLog.iteration != null && (
                  <Badge variant="secondary">
                    Iter #{currentLog.iteration}
                  </Badge>
                )}
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {currentLog.timestamp ? new Date(currentLog.timestamp).toLocaleTimeString() : "Unknown"}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="whitespace-pre-wrap text-sm">
                {currentLog.content}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Mini Timeline */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Timeline Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[150px]">
            <div className="space-y-1">
              {sortedLogs.map((log, index) => {
                const Icon = AGENT_ICONS[log.agentType] || Bot;
                const isActive = index === currentIndex;
                const isPast = index < currentIndex;

                return (
                  <button
                    key={log.id}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg p-2 text-left text-sm transition-colors",
                      isActive && "bg-primary/10 border border-primary",
                      isPast && !isActive && "opacity-50",
                      !isActive && "hover:bg-muted"
                    )}
                    onClick={() => {
                      setCurrentIndex(index);
                      setIsPlaying(false);
                    }}
                  >
                    <div
                      className={cn(
                        "flex h-6 w-6 items-center justify-center rounded-full",
                        AGENT_COLORS_TW[log.agentType] || "bg-gray-500"
                      )}
                    >
                      <Icon className="h-3 w-3 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="capitalize truncate">
                        {log.agentType.replace("_", " ")}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {getElapsedTime(log)}
                    </span>
                    {log.iteration !== null && (
                      <Badge variant="outline" className="text-xs">
                        #{log.iteration}
                      </Badge>
                    )}
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
