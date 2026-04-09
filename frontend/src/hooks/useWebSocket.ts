import { useEffect, useState } from "react";

import type { WorkflowEventMessage } from "../types/api";
import { useAppStore } from "../store";

export function useWorkflowWebSocket(enabled: boolean): { connected: boolean } {
  const consumeEvent = useAppStore((state) => state.consumeEvent);
  const appendLog = useAppStore((state) => state.appendLog);
  const setActiveBottomTab = useAppStore((state) => state.setActiveBottomTab);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as WorkflowEventMessage;
      consumeEvent(payload);
      if (payload.type.startsWith("block_") || payload.type.startsWith("workflow_")) {
        setActiveBottomTab("logs");
      }
      // Append a dedicated log entry for block_error events so the full error
      // text is visible in the Logs panel even if the user missed the node badge.
      if (payload.type === "block_error" && typeof payload.data.error === "string") {
        appendLog({
          timestamp: payload.timestamp,
          level: "error",
          message: `Block error [${payload.block_id ?? "unknown"}]: ${payload.data.error}`,
          workflow_id: payload.workflow_id ?? null,
          block_id: payload.block_id ?? null,
        });
      }
    };

    return () => {
      socket.close();
    };
  }, [appendLog, consumeEvent, enabled, setActiveBottomTab]);

  return { connected };
}
