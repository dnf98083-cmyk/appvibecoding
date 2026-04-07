import "dotenv/config";

export const config = {
  apiKey: process.env.OPENROUTER_API_KEY,
  baseUrl: "https://openrouter.ai/api/v1",
  models: {
    text: "qwen/qwen3.6-plus:free",
    vision: "google/gemma-3-27b-it:free",
  },
};

if (!config.apiKey) {
  throw new Error(".env 파일에 OPENROUTER_API_KEY가 없습니다.");
}
