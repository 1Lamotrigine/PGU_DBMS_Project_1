const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const TOKEN_KEY = "eq_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  // Mirror into a cookie so Next.js middleware can protect routes.
  document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=${
    60 * 60 * 2
  }; samesite=lax`;
  window.dispatchEvent(new Event("eq-auth-changed"));
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`;
  window.dispatchEvent(new Event("eq-auth-changed"));
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = options;
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      (data && data.error && data.error.message) ||
      (data && data.detail) ||
      `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data as T;
}

export const api = {
  register: (payload: { firstName: string; lastName: string; email: string; password: string }) =>
    apiRequest<{ token: string; user: UserProfile }>("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload: { email: string; password: string }) =>
    apiRequest<{ token: string; user: UserProfile }>("/auth/login", { method: "POST", body: payload, auth: false }),
  googleLogin: (credential: string) =>
    apiRequest<{ token: string; user: UserProfile; is_new_user: boolean }>("/auth/google", {
      method: "POST",
      body: { credential },
      auth: false,
    }),
  me: () => apiRequest<UserProfile>("/auth/me"),
  levels: () => apiRequest<Level[]>("/levels"),
  mission: (id: number) => apiRequest<Mission>(`/missions/${id}`),
  missionVocabulary: (id: number) =>
    apiRequest<VocabularyItem[]>(`/missions/${id}/vocabulary`),
  recommended: () => apiRequest<(Mission & { is_completed?: boolean })[]>("/missions/recommended"),
  calibration: (answers: { question_id: number; selected_option: string }[]) =>
    apiRequest<{ cefr_level: string; total_xp: number; auto_completed_missions: number }>("/calibration/submit", {
      method: "POST",
      body: { answers },
    }),
  calibrationQuestions: () =>
    apiRequest<CalibrationQuestion[]>("/calibration/questions"),
  startAttempt: (id: number, module: "test" | "pronunciation" | "game" | "grammar" = "game") =>
    apiRequest<{
      attempt_id: number;
      module: string;
      items?: VocabularyItem[];
      questions?: GrammarQuestion[];
    }>(`/missions/${id}/start`, {
      method: "POST",
      body: { module },
    }),
  submitTests: (id: number, answers: { question_id: number; option_id?: number; text?: string }[]) =>
    apiRequest<{ tests_passed: boolean; percent: number; passed: boolean }>(`/missions/${id}/submit-tests`, {
      method: "POST",
      body: { answers },
    }),
  submitPronunciation: (id: number, answers: { item_id: number; word: string }[]) =>
    apiRequest<{ pronunciation_passed: boolean; percent: number; passed: boolean }>(
      `/missions/${id}/submit-pronunciation`,
      { method: "POST", body: { answers } },
    ),
  submitGame: (id: number, attemptId: number, answers: { item_id: number; word: string }[]) =>
    apiRequest<{ success: boolean; percent: number; xp_awarded: number; total_xp: number }>(
      `/missions/${id}/submit-game`,
      { method: "POST", body: { attempt_id: attemptId, answers } },
    ),
  submitGrammar: (id: number, attemptId: number, answers: { question_id: number; option_id: number }[]) =>
    apiRequest<{
      success: boolean;
      passed: boolean;
      percent: number;
      xp_awarded: number;
      total_xp: number;
      mission_completed: boolean;
    }>(`/missions/${id}/submit-grammar`, {
      method: "POST",
      body: { attempt_id: attemptId, answers },
    }),
  checkGrammar: (id: number, questionId: number, optionId: number) =>
    apiRequest<{ question_id: number; option_id: number; correct: boolean }>(
      `/missions/${id}/check-grammar`,
      { method: "POST", body: { question_id: questionId, option_id: optionId } },
    ),
  myProgress: () => apiRequest<Progress>("/users/me/progress"),
  leaderboard: (limit = 10) => apiRequest<LeaderboardEntry[]>(`/users/leaderboard?limit=${limit}`),
  createMission: (payload: unknown) => apiRequest<Mission>("/missions", { method: "POST", body: payload }),
  updateMission: (id: number, payload: unknown) =>
    apiRequest<Mission>(`/missions/${id}`, { method: "PUT", body: payload }),
  deleteMission: (id: number) => apiRequest<{ deleted: boolean }>(`/missions/${id}`, { method: "DELETE" }),

  // ---- admin: tasks / questions / options ----
  createTask: (missionId: number, payload: unknown) =>
    apiRequest<Task>(`/missions/${missionId}/tasks`, { method: "POST", body: payload }),
  updateTask: (taskId: number, payload: unknown) =>
    apiRequest<Task>(`/missions/tasks/${taskId}`, { method: "PUT", body: payload }),
  deleteTask: (taskId: number) =>
    apiRequest<{ deleted: boolean }>(`/missions/tasks/${taskId}`, { method: "DELETE" }),

  createQuestion: (taskId: number, payload: unknown) =>
    apiRequest<Question>(`/missions/tasks/${taskId}/questions`, { method: "POST", body: payload }),
  updateQuestion: (questionId: number, payload: unknown) =>
    apiRequest<Question>(`/missions/questions/${questionId}`, { method: "PUT", body: payload }),
  deleteQuestion: (questionId: number) =>
    apiRequest<{ deleted: boolean }>(`/missions/questions/${questionId}`, { method: "DELETE" }),

  createOption: (questionId: number, payload: unknown) =>
    apiRequest<QuestionOption>(`/missions/questions/${questionId}/options`, { method: "POST", body: payload }),
  updateOption: (optionId: number, payload: unknown) =>
    apiRequest<QuestionOption>(`/missions/options/${optionId}`, { method: "PUT", body: payload }),
  deleteOption: (optionId: number) =>
    apiRequest<{ deleted: boolean }>(`/missions/options/${optionId}`, { method: "DELETE" }),

  // ---- admin: vocabulary ----
  levelVocabulary: (levelId: number) => apiRequest<VocabularyItem[]>(`/levels/${levelId}/vocabulary`),
  createVocabulary: (levelId: number, payload: unknown) =>
    apiRequest<VocabularyItem>(`/levels/${levelId}/vocabulary`, { method: "POST", body: payload }),
  updateVocabulary: (vocabId: number, payload: unknown) =>
    apiRequest<VocabularyItem>(`/vocabulary/${vocabId}`, { method: "PUT", body: payload }),
  deleteVocabulary: (vocabId: number) =>
    apiRequest<{ deleted: boolean }>(`/vocabulary/${vocabId}`, { method: "DELETE" }),
};

export type UserProfile = {
  id: number;
  name: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  cefr_level: string;
  unlocked_level_rank: number;
  total_xp: number;
  is_calibrated: boolean;
  // False for accounts created through Google Sign-In without a password.
  has_password?: boolean;
};

export type Task = {
  id: number;
  title: string;
  type: string;
  description?: string | null;
  order_number?: number;
  time_limit?: number | null;
  xp_reward_first: number;
  xp_reward_repeat: number;
  questions?: Question[];
};

export type QuestionOption = {
  id: number;
  option_text: string;
  translation_ru: string | null;
  image_url: string | null;
  // Only present for teachers; students never receive the correct answer.
  is_correct?: boolean;
};

export type Question = {
  id: number;
  question_text: string;
  question_type: string;
  options: QuestionOption[];
};

export type GrammarQuestion = {
  id: number;
  question_text: string;
  question_type: string;
  options: QuestionOption[];
};

export type Mission = {
  id: number;
  level_id: number;
  order_index: number;
  title: string;
  description: string | null;
  is_active: boolean;
  locked?: boolean;
  tasks: Task[];
  progress?: {
    is_completed: boolean;
    tests_passed: boolean;
    pronunciation_passed: boolean;
    game_passed?: boolean;
    grammar_passed?: boolean;
    best_score_percentage: number;
    completion_count: number;
    xp_earned?: number;
  };
};

export type Level = {
  id: number;
  code: string;
  title: string;
  locked: boolean;
  missions: Mission[];
};

export type Progress = {
  user_id: number;
  name: string;
  cefr_level: string;
  level: number;
  unlocked_level_rank: number;
  total_xp: number;
  is_calibrated: boolean;
  completed_missions: number;
  available_missions: number;
  total_missions: number;
};

export type LeaderboardEntry = {
  rank: number;
  name: string;
  total_xp: number;
};

export type CalibrationQuestion = {
  id: number;
  question_text: string;
  cefr_level: string;
  options: { A: string; B: string; C: string; D: string };
};

export type VocabularyItem = {
  id: number;
  word_en: string;
  word_ru: string;
  transcription: string | null;
  image_url: string | null;
};
