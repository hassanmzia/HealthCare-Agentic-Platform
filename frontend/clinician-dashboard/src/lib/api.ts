import { api } from "./http";

export type Recommendation = {
  id: number;
  patient_id?: string;
  created_at: string;
  severity?: "info" | "warning" | "critical";
  title: string;
  summary: string;
  rationale?: string;
  evidence?: Array<{ source: string; snippet: string }>;
};

export async function fetchRecommendations(patientId?: string) {
  const params = patientId ? { patient_id: patientId } : {};
  const res = await api.get<Recommendation[]>("/api/v1/recommendations/", { params });
  return res.data;
}

