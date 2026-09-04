import { describe, expect, it } from "vitest";

import {
  formatDateTime,
  formatDuration,
  formatMs,
  formatPercent,
  formatRelative,
} from "./format";

describe("formatPercent", () => {
  it("formats a fraction as a percentage", () => {
    expect(formatPercent(0.4567)).toBe("45.7%");
  });

  it("respects the digits argument", () => {
    expect(formatPercent(0.4567, 0)).toBe("46%");
  });

  it("returns an em dash for null or undefined", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(undefined)).toBe("—");
  });
});

describe("formatMs", () => {
  it("rounds to the nearest millisecond", () => {
    expect(formatMs(123.6)).toBe("124ms");
  });

  it("returns an em dash for null or undefined", () => {
    expect(formatMs(null)).toBe("—");
  });
});

describe("formatDateTime", () => {
  it("returns an em dash for null", () => {
    expect(formatDateTime(null)).toBe("—");
  });

  it("returns a non-empty string for a valid ISO timestamp", () => {
    expect(formatDateTime("2026-01-01T00:00:00Z").length).toBeGreaterThan(0);
  });
});

describe("formatRelative", () => {
  it("returns an em dash for null", () => {
    expect(formatRelative(null)).toBe("—");
  });

  it("reports very recent timestamps as just now", () => {
    expect(formatRelative(new Date().toISOString())).toBe("just now");
  });
});

describe("formatDuration", () => {
  it("formats sub-minute durations in seconds", () => {
    const start = new Date(Date.now() - 30_000).toISOString();
    expect(formatDuration(start, null)).toMatch(/^\d+s$/);
  });

  it("formats multi-minute durations as minutes and seconds", () => {
    const start = new Date("2026-01-01T00:00:00Z").toISOString();
    const end = new Date("2026-01-01T00:02:15Z").toISOString();
    expect(formatDuration(start, end)).toBe("2m 15s");
  });
});
