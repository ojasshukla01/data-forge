import { render, screen } from "@testing-library/react";
import { PipelineFlowGraph } from "./PipelineFlowGraph";

describe("PipelineFlowGraph", () => {
  it("renders default stages", () => {
    render(<PipelineFlowGraph />);
    expect(screen.getByText("Generation")).toBeInTheDocument();
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("renders custom stages", () => {
    render(
      <PipelineFlowGraph
        stages={[
          { id: "a", label: "Stage A" },
          { id: "b", label: "Stage B" },
        ]}
      />
    );
    expect(screen.getByText("Stage A")).toBeInTheDocument();
    expect(screen.getByText("Stage B")).toBeInTheDocument();
  });
});
