import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/components/MetricCard";

describe("MetricCard", () => {
  it("renders the label and a compact value", () => {
    render(<MetricCard label="Total Events" value={12345} />);
    expect(screen.getByText("Total Events")).toBeInTheDocument();
    expect(screen.getByText("12.3K")).toBeInTheDocument();
  });

  it("renders an optional hint", () => {
    render(<MetricCard label="Unique Users" value={42} hint="last 14 days" />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("last 14 days")).toBeInTheDocument();
  });
});
