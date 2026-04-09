import { render, waitFor, screen, fireEvent, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  cleanup();
});

import { DataPreview } from "./DataPreview";

describe("DataPreview", () => {
  it("requests previews lazily for selected output refs", async () => {
    const onLoadPreview = vi.fn(async () => {});

    render(
      <DataPreview
        blockOutputs={{
          "node-1": {
            output: {
              data_ref: "data-123",
            },
          },
        }}
        onCancelSelected={() => {}}
        onLoadPreview={onLoadPreview}
        onStartFromHere={() => {}}
        previewCache={{}}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Process Block"
      />,
    );

    await waitFor(() => {
      expect(onLoadPreview).toHaveBeenCalledWith("data-123");
    });
  });

  it("renders image preview with zoom controls", () => {
    render(
      <DataPreview
        blockOutputs={{
          "node-1": {
            output: { data_ref: "img-ref" },
          },
        }}
        onCancelSelected={() => {}}
        onLoadPreview={vi.fn(async () => {})}
        onStartFromHere={() => {}}
        previewCache={{
          "img-ref": {
            preview: {
              kind: "image",
              src: "data:image/png;base64,abc",
              shape: [100, 200, 3],
            },
          } as never,
        }}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Image Block"
      />,
    );

    // Zoom controls
    expect(screen.getByRole("button", { name: /zoom in/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /zoom out/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reset/i })).toBeInTheDocument();

    // Brightness and contrast sliders
    expect(screen.getByRole("slider", { name: /brightness/i })).toBeInTheDocument();
    expect(screen.getByRole("slider", { name: /contrast/i })).toBeInTheDocument();

    // Colormap selector
    expect(screen.getByRole("combobox", { name: /colormap/i })).toBeInTheDocument();

    // Shape info
    expect(screen.getByText(/100 × 200 × 3/)).toBeInTheDocument();
  });

  it("zoom in button increases scale display", () => {
    render(
      <DataPreview
        blockOutputs={{ "node-1": { output: { data_ref: "img-ref" } } }}
        onCancelSelected={() => {}}
        onLoadPreview={vi.fn(async () => {})}
        onStartFromHere={() => {}}
        previewCache={{
          "img-ref": {
            preview: { kind: "image", src: "data:image/png;base64,abc" },
          } as never,
        }}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Image Block"
      />,
    );

    // Default zoom is 100%
    expect(screen.getByText("100%")).toBeInTheDocument();

    // Click zoom in
    fireEvent.click(screen.getByRole("button", { name: /zoom in/i }));

    // Scale should have increased (125%)
    expect(screen.getByText("125%")).toBeInTheDocument();
  });

  it("renders table preview with sticky headers and row/column count", () => {
    render(
      <DataPreview
        blockOutputs={{ "node-1": { output: { data_ref: "tbl-ref" } } }}
        onCancelSelected={() => {}}
        onLoadPreview={vi.fn(async () => {})}
        onStartFromHere={() => {}}
        previewCache={{
          "tbl-ref": {
            preview: {
              kind: "table",
              columns: ["A", "B", "C"],
              rows: [
                { A: 1, B: 2, C: 3 },
                { A: 4, B: 5, C: 6 },
              ],
            },
          } as never,
        }}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Table Block"
      />,
    );

    // Row/column count header
    expect(screen.getByText(/2 rows × 3 columns/)).toBeInTheDocument();

    // Column headers
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();

    // Data cells
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
  });
});
