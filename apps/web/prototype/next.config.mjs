import { fileURLToPath } from "node:url";

export default {
  poweredByHeader: false,
  reactStrictMode: true,
  devIndicators: false,
  allowedDevOrigins: ["127.0.0.1"],
  turbopack: { root: fileURLToPath(new URL("..", import.meta.url)) },
};
