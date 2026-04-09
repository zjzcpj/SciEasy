import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "../lib/api";
import { BottomPanel } from "./BottomPanel";

vi.mock("../lib/api", () => ({
  api: {
    browseDirectory: vi.fn(),
    browseFiles: vi.fn(),
  },
}));

describe("BottomPanel", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders config inputs from schema and emits config updates", () => {
    const onUpdateConfig = vi.fn();

    render(
      <BottomPanel
        activeTab="config"
        aiError={null}
        aiLoading={false}
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

  it("shows a browse button for IO path fields and uses file browsing for loaders", async () => {
    const onUpdateConfig = vi.fn();
    vi.mocked(api.browseFiles).mockResolvedValue({ paths: ["/tmp/sample.tiff"] });

    render(
      <BottomPanel
        activeTab="config"
        aiError={null}
        aiLoading={false}
        chatMessages={[]}
        logEntries={[]}
        onSendChat={() => {}}
        onTabChange={() => {}}
        onUpdateConfig={onUpdateConfig}
        selectedNode={{
          id: "load-1",
          block_type: "imaging.load_image",
          config: { params: { path: "" } },
        }}
        selectedSchema={{
          name: "Load Image",
          type_name: "imaging.load_image",
          category: "io",
          description: "",
          version: "0.1.0",
          input_ports: [],
          output_ports: [],
          direction: "input",
          config_schema: {
            properties: {
              path: {
                type: "string",
                title: "Path",
                ui_priority: 0,
              },
            },
          },
          type_hierarchy: [],
        }}
      />,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Browse" })[0]);
    await waitFor(() => {
      expect(api.browseFiles).toHaveBeenCalledTimes(1);
      expect(onUpdateConfig).toHaveBeenCalledWith({ path: "/tmp/sample.tiff" });
    });
  });

  it("uses directory browsing for IO output blocks", async () => {
    const onUpdateConfig = vi.fn();
    vi.mocked(api.browseDirectory).mockResolvedValue({ path: "/tmp/output" });

    render(
      <BottomPanel
        activeTab="config"
        aiError={null}
        aiLoading={false}
        chatMessages={[]}
        logEntries={[]}
        onSendChat={() => {}}
        onTabChange={() => {}}
        onUpdateConfig={onUpdateConfig}
        selectedNode={{
          id: "save-1",
          block_type: "imaging.save_image",
          config: { params: { path: "" } },
        }}
        selectedSchema={{
          name: "Save Image",
          type_name: "imaging.save_image",
          category: "io",
          description: "",
          version: "0.1.0",
          input_ports: [],
          output_ports: [],
          direction: "output",
          config_schema: {
            properties: {
              path: {
                type: "string",
                title: "Path",
                ui_priority: 0,
              },
            },
          },
          type_hierarchy: [],
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Browse" }));
    await waitFor(() => {
      expect(api.browseDirectory).toHaveBeenCalledTimes(1);
      expect(onUpdateConfig).toHaveBeenCalledWith({ path: "/tmp/output" });
    });
  });
});
