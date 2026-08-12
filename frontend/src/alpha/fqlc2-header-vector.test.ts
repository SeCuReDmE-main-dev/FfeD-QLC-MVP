// @vitest-environment node

import { decode } from "cbor-x";
import { describe, expect, it } from "vitest";

import vector from "./fixtures/fqlc2-header-vector.json";

function decodeBase64(value: string): Uint8Array {
  return Uint8Array.from(atob(value), (character) => character.charCodeAt(0));
}

describe("FQLC2 Python-to-TypeScript header vector", () => {
  it("decodes the deterministic RFC 8949 header without changing its hierarchy", () => {
    const header = decode(decodeBase64(vector.header_base64)) as {
      version: number;
      suite: string;
      context: { hierarchy: string; key_material: boolean };
      stanzas: unknown[];
    };

    expect(header.version).toBe(vector.expected.version);
    expect(header.suite).toBe(vector.expected.suite);
    expect(header.stanzas).toHaveLength(vector.expected.recipient_count);
    expect(header.context.hierarchy).toBe(vector.expected.hierarchy);
    expect(header.context.key_material).toBe(vector.expected.key_material);
  });
});
