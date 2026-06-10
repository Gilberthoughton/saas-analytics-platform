import { describe, expect, it } from "vitest";
import {
  cn,
  formatCompact,
  formatDateTime,
  formatNumber,
  shortDate,
  titleCase,
} from "@/lib/utils";

describe("cn", () => {
  it("joins truthy values and drops falsy ones", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });
});

describe("number formatting", () => {
  it("formats with separators", () => {
    expect(formatNumber(1234567)).toBe("1,234,567");
  });
  it("formats compactly", () => {
    expect(formatCompact(12345)).toBe("12.3K");
    expect(formatCompact(2_000_000)).toBe("2M");
  });
});

describe("date helpers (UTC, hydration-safe)", () => {
  it("formats a datetime in UTC", () => {
    // Pinned to UTC, so the result is independent of the host timezone.
    expect(formatDateTime("2025-03-05T14:30:00Z")).toBe("Mar 5, 2025, 2:30 PM");
  });
  it("returns an em dash for invalid input", () => {
    expect(formatDateTime("nope")).toBe("—");
  });
  it("formats a short M/D tick in UTC", () => {
    expect(shortDate("2025-03-05")).toBe("3/5");
  });
});

describe("titleCase", () => {
  it("humanizes dotted/underscored actions", () => {
    expect(titleCase("api_key.create")).toBe("Api Key Create");
    expect(titleCase("user.register")).toBe("User Register");
  });
});
