type WebMCPContext = { nonce?: string; signal?: AbortSignal };
export async function registerSecuredMeWebMCP(): Promise<void> {
  const modelContext = (document as Document & { modelContext?: { registerTool?: (tool: unknown) => void } }).modelContext;
  if (!modelContext?.registerTool) return;
  const response = await fetch("/api/v1/webmcp/manifest", { credentials: "same-origin" });
  if (!response.ok) return;
  const manifest = await response.json();
  const root = document.documentElement;
  Object.entries(manifest.product?.theme?.tokens || {}).forEach(([key, value]) => root.style.setProperty(`--securedme-${key}`, String(value)));
  root.dataset.securedmeProduct = manifest.product.slug;
  for (const descriptor of manifest.tools) {
    modelContext.registerTool({name: descriptor.name, description: descriptor.description, inputSchema: descriptor.inputSchema,
      execute: async (args: Record<string, unknown> = {}, context: WebMCPContext = {}) => {
        const result = await fetch("/api/v1/webmcp/invoke", {method: "POST", credentials: "same-origin", headers: {"Content-Type": "application/json", "X-SecuredMe-WebMCP": "1"}, body: JSON.stringify({name: descriptor.name, arguments: args, nonce: context.nonce}), signal: context.signal});
        const payload = await result.json();
        if (!result.ok) throw new Error(payload.error_code || "WEBMCP_REJECTED");
        return payload;
      }});
  }
}
