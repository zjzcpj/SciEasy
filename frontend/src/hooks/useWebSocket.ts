import { useEffect, useState } from "react";

import type { WorkflowEventMessage } from "../types/api";
import { useAppStore } from "../store";

export function useWorkflowWebSocket(enabled: boolean): { connected: boolean } {
  const consumeEvent = useAppStore((state) => state.consumeEvent);
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
    };

    return () => {
      socket.close();
    };
  }, [consumeEvent, enabled, setActiveBottomTab]);

  return { connected };
}
