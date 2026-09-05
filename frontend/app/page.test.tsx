import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Home from "./page";

describe("job finder page", () => {
  it("shows the search controls", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ items: [], page: 1, page_size: 12, total: 0 }) })));
    render(<Home />);
    expect(screen.getByRole("heading", { name: "Find work that fits." })).toBeDefined();
    expect(screen.getByPlaceholderText("Title, company, or keyword")).toBeDefined();
    expect(screen.getByRole("button", { name: "Search jobs" })).toBeDefined();
  });
});
