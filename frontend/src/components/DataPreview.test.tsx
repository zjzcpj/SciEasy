import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
});
