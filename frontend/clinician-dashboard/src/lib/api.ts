import axios from "axios";
import { api } from "./http";

// Orchestrator API for AI services
const orchestrator = axios.create({
  baseURL: import.meta.env.VITE_ORCH_BASE || import.meta.env.VITE_ORCHESTRATOR_BASE || "http://localhost:8003",
  timeout: 60000, // Longer timeout for AI processing
});

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

// Clinical Assessment Types
export type ClinicalFinding = {
  type: string;
  name: string;
  value: string | number;
  unit?: string;
  status: "normal" | "abnormal" | "critical";
  interpretation: string;
  source: string;
  reference_range?: string;
};

export type DiagnosisRecommendation = {
  diagnosis: string;
  icd10_code: string;
  confidence: number;
  supporting_findings: ClinicalFinding[];
  rationale: string;
  differential_diagnoses?: Array<{
    diagnosis: string;
    icd10: string;
    confidence: number;
    rationale: string;
  }>;
};

export type TreatmentRecommendation = {
  treatment_type: string;
  description: string;
  priority: string;
  rationale: string;
  cpt_code?: string;
  contraindications?: string[];
  monitoring?: string[];
};

export type ClinicalAssessment = {
  patient_summary: {
    patient_id: string;
    name?: string;
    age?: number;
    sex?: string;
  };
  findings: ClinicalFinding[];
  critical_findings: ClinicalFinding[];
  diagnoses: DiagnosisRecommendation[];
  treatments: TreatmentRecommendation[];
  icd10_codes: Array<{ code: string; description: string; category: string; confidence: number }>;
  cpt_codes: Array<{ code: string; description: string; category: string }>;
  confidence: number;
  reasoning: string[];
  warnings: string[];
  requires_human_review: boolean;
  review_reason?: string;
  persisted_recommendation_id?: number;
};

export type AssessmentResponse = {
  success: boolean;
  patient_id: string;
  assessment?: ClinicalAssessment;
  error?: string;
  llm_provider?: string;
};

export type LLMStatus = {
  status: string;
  primary_provider?: string;
  available_providers?: string[];
  config?: {
    claude_model: string;
    ollama_model: string;
    ollama_base_url: string;
    temperature: number;
    max_tokens: number;
  };
  error?: string;
};

export type AgentInfo = {
  agent_id: string;
  name: string;
  description: string;
  version: string;
  specialties: string[];
  capabilities: Array<{
    name: string;
    description: string;
  }>;
};

// Fetch comprehensive clinical assessment
export async function fetchClinicalAssessment(patientId: string, fhirId?: string): Promise<AssessmentResponse> {
  const res = await orchestrator.post<AssessmentResponse>("/api/v1/assess", {
    patient_id: patientId,
    fhir_id: fhirId,
    include_diagnoses: true,
    include_treatments: true,
    include_codes: true,
  });
  return res.data;
}

// Get quick assessment via GET
export async function getQuickAssessment(patientId: string): Promise<AssessmentResponse> {
  const res = await orchestrator.get<AssessmentResponse>(`/api/v1/assess/${patientId}`);
  return res.data;
}

// Get LLM status
export async function fetchLLMStatus(): Promise<LLMStatus> {
  const res = await orchestrator.get<LLMStatus>("/api/v1/llm/status");
  return res.data;
}

// Switch LLM provider
export async function switchLLMProvider(provider: string): Promise<{ success: boolean; new_provider: string }> {
  const res = await orchestrator.post(`/api/v1/llm/switch?provider=${provider}`);
  return res.data;
}

// Get available agents
export async function fetchAgents(): Promise<{ agents: AgentInfo[] }> {
  const res = await orchestrator.get<{ agents: AgentInfo[] }>("/api/v1/agents");
  return res.data;
}

// Get MCP server status
export async function fetchMCPStatus(): Promise<{ mcp_servers: Record<string, { url: string; status: string; error?: string }> }> {
  const res = await orchestrator.get("/api/v1/mcp/status");
  return res.data;
}
