export const getAIMessage = async (userQuery, sessionId, onToken, onDone) => {
  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userQuery, session_id: sessionId }),
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const raw = line.slice(5).trim();
      try {
        const event = JSON.parse(raw);
        if (event.type === "token") {
          const text =
            typeof event.content === "string"
              ? event.content
              : Array.isArray(event.content)
              ? event.content
                  .filter((b) => b.type === "text")
                  .map((b) => b.text)
                  .join("")
              : "";
          if (text) onToken(text);
        } else if (event.type === "done") {
          onDone(event.parts ?? []);
        }
      } catch {
        // skip malformed lines
      }
    }
  }
};
