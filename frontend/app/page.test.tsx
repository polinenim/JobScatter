import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Home from "./page";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("profile home page", () => {
  it("shows the profile summary and primary actions immediately", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "Find your next opportunity." })).toBeDefined();
    expect(screen.getByText("M.Sc. Information Technology")).toBeDefined();
    expect(screen.getByText("AI / ML, Software, Data")).toBeDefined();
    expect(screen.getByText("Internship, Trainee, Graduate, Junior")).toBeDefined();
    expect(screen.getByText("Finland")).toBeDefined();
    expect(screen.getByRole("button", { name: "FETCH JOBS" })).toBeDefined();
    expect(screen.getByRole("button", { name: "SCHEDULE" })).toBeDefined();
    expect(screen.getByRole("button", { name: "EDIT PROFILE" })).toBeDefined();
  });

  it("does not show job results until fetch is executed", () => {
    vi.stubEnv("NEXT_PUBLIC_CANDIDATE_ID", "candidate-1");
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    render(<Home />);

    expect(screen.queryByText("Your latest search is ready.")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "FETCH JOBS" }));
    expect(screen.getByRole("button", { name: "FETCHING..." }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByRole("status").textContent).toContain("Refreshing job sources");
  });

  it("shows a clear message when the backend cannot be reached", async () => {
    vi.stubEnv("NEXT_PUBLIC_CANDIDATE_ID", "candidate-1");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "FETCH JOBS" }));

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Unable to reach the JobScatter API. Check that the backend is running and try again.",
    );
    expect(screen.getByRole("button", { name: "FETCH JOBS" }).hasAttribute("disabled")).toBe(false);
  });

  it("shows a useful API error and allows the user to retry", async () => {
    vi.stubEnv("NEXT_PUBLIC_CANDIDATE_ID", "candidate-1");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Confirmed candidate profile not found" }),
    }));
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "FETCH JOBS" }));

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Confirmed candidate profile not found",
    );
    expect(screen.getByRole("button", { name: "FETCH JOBS" }).hasAttribute("disabled")).toBe(false);
  });

  it("shows the minimal result row and PDF action after fetch", async () => {
    vi.stubEnv("NEXT_PUBLIC_CANDIDATE_ID", "candidate-1");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        total: 1,
        items: [{
          company_name: "Example Co",
          job_title: "Software Engineer",
          posted_at: "2026-09-05T12:00:00Z",
          job_link: "https://jobs.example/1",
        }],
      }),
    }));

    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: "FETCH JOBS" }));

    expect(await screen.findByText("Example Co")).toBeDefined();
    expect(screen.getByText("Software Engineer")).toBeDefined();
    expect(screen.getByRole("link", { name: "APPLY" }).getAttribute("href")).toBe("https://jobs.example/1");
    expect(screen.getByRole("button", { name: "DOWNLOAD PDF" })).toBeDefined();
  });

  it("opens the editor and saves an updated profile field", () => {
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "EDIT PROFILE" }));
    expect(screen.getByRole("heading", { name: "Shape your profile" })).toBeDefined();
    const education = screen.getByLabelText("Education");
    fireEvent.change(education, { target: { value: "MSc Computer Science" } });
    fireEvent.click(screen.getByRole("button", { name: "SAVE PROFILE" }));

    expect(screen.getByText("MSc Computer Science")).toBeDefined();
    expect(screen.getByRole("button", { name: "EDIT PROFILE" })).toBeDefined();
  });
});
