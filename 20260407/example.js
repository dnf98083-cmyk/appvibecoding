import { config } from "./config.js";

async function callOpenRouter(model, messages) {
  const res = await fetch(`${config.baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model, messages }),
  });
  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error(`[${res.status}] ${data.error?.message}`);
  }
  if (!data.choices?.length) {
    throw new Error("응답에 choices가 없습니다: " + JSON.stringify(data));
  }
  return data.choices[0].message.content;
}

// 텍스트 생성 테스트
async function testText() {
  console.log("\n[텍스트 생성] 모델:", config.models.text);
  const prompt = "인공지능이란 무엇인지 한국어로 두 문장으로 설명해줘.";
  console.log("입력:", prompt);
  const reply = await callOpenRouter(config.models.text, [
    { role: "user", content: prompt },
  ]);
  console.log("응답:", reply);
}

// 이미지 인식 테스트
async function testVision() {
  console.log("\n[이미지 인식] 모델:", config.models.vision);
  // 1x1 빨간 픽셀 PNG (base64)
  const redPixelB64 =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg==";
  console.log("입력: 1x1 빨간 픽셀 이미지");
  const reply = await callOpenRouter(config.models.vision, [
    {
      role: "user",
      content: [
        {
          type: "image_url",
          image_url: { url: `data:image/png;base64,${redPixelB64}` },
        },
        { type: "text", text: "이 이미지에서 무엇이 보이나요? 한국어로 설명해주세요." },
      ],
    },
  ]);
  console.log("응답:", reply);
}

// 실행
console.log("=".repeat(50));
console.log("  OpenRouter API 테스트");
console.log("=".repeat(50));

await testText().catch((e) => console.error("텍스트 오류:", e.message));
await testVision().catch((e) => console.error("이미지 오류:", e.message));

console.log("\n" + "=".repeat(50));
console.log("  테스트 완료");
console.log("=".repeat(50));
