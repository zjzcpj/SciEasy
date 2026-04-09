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

  it("renders image preview with zoom controls and LUT swatches", () => {
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

    // Min/Max display range sliders
    expect(screen.getByRole("slider", { name: /display minimum/i })).toBeInTheDocument();
    expect(screen.getByRole("slider", { name: /display maximum/i })).toBeInTheDocument();

    // LUT gradient swatches (at least gray and fire)
    expect(screen.getByRole("button", { name: /LUT gray/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /LUT fire/i })).toBeInTheDocument();

    // Info badge showing shape and zoom
    const badge = screen.getByTestId("image-info-badge");
    expect(badge).toHaveTextContent(/100 × 200 × 3/);
    expect(badge).toHaveTextContent(/100%/);
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

    // Default zoom is 100% (shown in controls text)
    const zoomTexts = screen.getAllByText("100%");
    expect(zoomTexts.length).toBeGreaterThanOrEqual(1);

    // Click zoom in
    fireEvent.click(screen.getByRole("button", { name: /zoom in/i }));

    // Scale should have increased (125% in controls)
    const updatedTexts = screen.getAllByText("125%");
    expect(updatedTexts.length).toBeGreaterThanOrEqual(1);
  });

  it("renders table preview with compact formatting and row/column count", () => {
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
                { A: 1, B: 2.12345, C: 3 },
                { A: 4, B: 5, C: 6.789012 },
              ],
            },
          } as never,
        }}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Table Block"
      />,
    );

    // Row/column count
    expect(screen.getByText(/2 rows × 3 columns/)).toBeInTheDocument();

    // Column headers
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();

    // Integer cells remain integers
    expect(screen.getByText("1")).toBeInTheDocument();

    // Floating-point cells formatted to 4 decimals
    expect(screen.getByText("2.1235")).toBeInTheDocument();
    expect(screen.getByText("6.7890")).toBeInTheDocument();
  });

  it("shows truncation label when 100+ rows", () => {
    const manyRows = Array.from({ length: 100 }, (_, i) => ({ A: i, B: i * 2 }));

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
              columns: ["A", "B"],
              rows: manyRows,
              row_count: 100,
            },
          } as never,
        }}
        previewLoading={{}}
        selectedNodeId="node-1"
        selectedNodeLabel="Table Block"
      />,
    );

    // Should indicate truncation
    expect(screen.getByText(/Showing 100 of 100\+/)).toBeInTheDocument();
  });
});
