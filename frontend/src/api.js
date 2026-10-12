const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken() {
  try { return localStorage.getItem("token"); } catch { return null; }
}
export function setToken(t) {
  try { t ? localStorage.setItem("token", t) : localStorage.removeItem("token"); } catch { /* storage unavailable */ }
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }
  if (res.status === 401 && token) {
    setToken(null);
    window.dispatchEvent(new Event("auth-expired"));
  }
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const d = data?.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? "Please check the details you entered." : "Something went wrong.");
  }
  return data;
}

export const api = {
  signup: (b) => request("/auth/signup", { method: "POST", body: b }),
  login: (b) => request("/auth/login", { method: "POST", body: b }),
  me: () => request("/me"),
  deleteAccount: () => request("/me", { method: "DELETE" }),
  chat: (b) => request("/chat", { method: "POST", body: b }),
  conversations: () => request("/conversations"),
  conversation: (id) => request(`/conversations/${id}`),
  deleteConversation: (id) => request(`/conversations/${id}`, { method: "DELETE" }),
  helplines: (lang) => request(`/helplines?lang=${lang}`),
  quote: () => request("/quote"),
};
