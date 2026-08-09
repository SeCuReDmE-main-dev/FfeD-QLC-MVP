import { describe, expect, it } from "vitest";
import { assertCredentialBlind, CONTRACT_IDS } from "./contracts";

describe("alpha contracts", () => {
  it("matches the Python alpha schema registry", () => {
    expect(CONTRACT_IDS).toHaveLength(10);
    expect(CONTRACT_IDS).toContain("ffed.qlc.vigil_report.v1");
  });

  it("rejects credential-bearing payloads", () => {
    expect(() => assertCredentialBlind({ evidence: { api_key: "forbidden" } })).toThrow("forbidden field");
    expect(() => assertCredentialBlind({ raw_secret_stored: false })).not.toThrow();
  });
});

