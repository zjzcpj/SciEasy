import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BottomPanel } from "./BottomPanel";

describe("BottomPanel", () => {
  it("renders config inputs from schema and emits config updates", () => {
    const onUpdateConfig = vi.fn();

    render(
      <BottomPanel
        activeTab="config"
        chatMessages={[]}
        logEntries={[]}
        onSendChat={() => {}}
        onTabChange={() => {}}
        onUpdateConfig={onUpdateConfig}
        selectedNode={{
          id: "node-1",
          block_type: "process_block",
          config: { params: { sleep_seconds: 1 } },
        }}
        selectedSchema={{
          name: "Process Block",
          type_name: "process_block",
          category: "process",
          description: "",
          version: "0.1.0",
          package_name: "",
          input_ports: [],
          output_ports: [],
          config_schema: {
            properties: {
              sleep_seconds: {
                type: "number",
                title: "Sleep seconds",
                ui_priority: 1,
                default: 0,
              },
            },
          },
          type_hierarchy: [],
        }}
      />,
    );

    const input = screen.getByDisplayValue("1");
    fireEvent.change(input, { target: { value: "4" } });
    expect(onUpdateConfig).toHaveBeenCalledWith({ sleep_seconds: 4 });
  });
});
