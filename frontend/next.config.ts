import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  assetPrefix: "",
  basePath: process.env.NODE_ENV === "development" ? "" : "/~s23238268",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
