import { useEffect, useRef, useState, useCallback } from "react";
import type { WSEvent, LogLine } from "@/types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

function classifyLine(msg: string): LogLine["type"] {
  if (msg.startsWith("[tool]")) return "tool";
  if (msg.startsWith("[error]")) return "error";
  if (msg.startsWith("[done]")) return "done";
  return "agent";
}

export function useTaskStream(taskId: string) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(`${WS_BASE}/tasks/${taskId}/ws`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data);
        setLogs((prev) => [
          ...prev,
          {
            id: `${event.ts}-${Math.random()}`,
            phase: event.phase,
            message: event.message,
            ts: event.ts,
            type: classifyLine(event.message),
          },
        ]);
      } catch {}
    };

    return ws;
  }, [taskId]);

  useEffect(() => {
    const ws = connect();
    return () => ws.close();
  }, [connect]);

  return { logs, connected };
}
