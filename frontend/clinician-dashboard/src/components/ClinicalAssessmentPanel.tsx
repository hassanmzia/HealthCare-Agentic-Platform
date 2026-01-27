import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchClinicalAssessment,
  fetchLLMStatus,
  type AssessmentResponse,
  type ClinicalAssessment,
  type ClinicalFinding,
  type DiagnosisRecommendation,
  type TreatmentRecommendation,
} from "../lib/api";

type Props = {
  patientId: string;
  fhirId?: string;
};

type ReviewState = {
  approvedDiagnoses: Set<number>;
  approvedTreatments: Set<number>;
  physicianNotes: string;
  reviewStatus: "pending" | "approved" | "rejected" | "modified";
};

export function ClinicalAssessmentPanel({ patientId, fhirId }: Props) {
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [showReasoning, setShowReasoning] = useState(false);
  const [reviewState, setReviewState] = useState<ReviewState>({
    approvedDiagnoses: new Set(),
    approvedTreatments: new Set(),
    physicianNotes: "",
    reviewStatus: "pending",
  });
  const [isReviewing, setIsReviewing] = useState(false);

  // Fetch LLM status
  const llmStatusQuery = useQuery({
    queryKey: ["llm-status"],
    queryFn: fetchLLMStatus,
    refetchInterval: 30000,
  });

  // Run assessment mutation
  const assessmentMutation = useMutation({
    mutationFn: () => fetchClinicalAssessment(patientId, fhirId),
    onSuccess: (data) => {
      setAssessment(data);
      // Initialize review state with all items approved by default
      if (data.assessment) {
        setReviewState({
          approvedDiagnoses: new Set(data.assessment.diagnoses.map((_, i) => i)),
          approvedTreatments: new Set(data.assessment.treatments.map((_, i) => i)),
          physicianNotes: "",
          reviewStatus: "pending",
        });
      }
      setIsReviewing(false);
    },
  });

  const handleStartReview = () => {
    setIsReviewing(true);
  };

  const handleToggleDiagnosis = (index: number) => {
    setReviewState(prev => {
      const newSet = new Set(prev.approvedDiagnoses);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return { ...prev, approvedDiagnoses: newSet };
    });
  };

  const handleToggleTreatment = (index: number) => {
    setReviewState(prev => {
      const newSet = new Set(prev.approvedTreatments);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return { ...prev, approvedTreatments: newSet };
    });
  };

  const handleSubmitReview = async (status: "approved" | "rejected" | "modified") => {
    // In a real app, this would call an API to save the review
    setReviewState(prev => ({ ...prev, reviewStatus: status }));
    setIsReviewing(false);

    // Show confirmation
    alert(`Review submitted as "${status}". In production, this would save to the database and create clinical documentation.`);
  };

  const cardStyle = { border: "1px solid #eee", borderRadius: 12, padding: 16, marginBottom: 16 };

  return (
    <div>
      {/* Header */}
      <div style={{ ...cardStyle, background: "#f0f9ff", border: "1px solid #bae6fd" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ margin: 0, color: "#0369a1" }}>AI Clinical Assessment</h3>
            <p style={{ margin: "8px 0 0", fontSize: 13, color: "#64748b" }}>
              Multi-agent system analyzes patient data to generate diagnoses and treatment recommendations
            </p>
          </div>
          <button
            onClick={() => assessmentMutation.mutate()}
            disabled={assessmentMutation.isPending || !fhirId}
            style={{
              padding: "12px 24px",
              borderRadius: 8,
              border: "none",
              background: assessmentMutation.isPending ? "#94a3b8" : "#0284c7",
              color: "white",
              cursor: assessmentMutation.isPending || !fhirId ? "not-allowed" : "pointer",
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {assessmentMutation.isPending ? "Analyzing..." : "Run Assessment"}
          </button>
        </div>

        {/* LLM Status */}
        {llmStatusQuery.data && (
          <div style={{ marginTop: 12, display: "flex", gap: 16, fontSize: 12 }}>
            <span style={{ color: "#64748b" }}>
              LLM: <strong style={{ color: llmStatusQuery.data.status === "available" ? "#059669" : "#dc2626" }}>
                {llmStatusQuery.data.primary_provider || "Not configured"}
              </strong>
            </span>
            {llmStatusQuery.data.config && (
              <span style={{ color: "#64748b" }}>
                Model: <strong>{llmStatusQuery.data.config.claude_model || llmStatusQuery.data.config.ollama_model}</strong>
              </span>
            )}
          </div>
        )}

        {!fhirId && (
          <div style={{ marginTop: 12, padding: 8, background: "#fef3c7", borderRadius: 6, fontSize: 13, color: "#92400e" }}>
            Patient must be synced to FHIR to run clinical assessment
          </div>
        )}
      </div>

      {/* Error Display */}
      {assessmentMutation.isError && (
        <div style={{ ...cardStyle, background: "#fef2f2", border: "1px solid #fecaca" }}>
          <h4 style={{ margin: 0, color: "#dc2626" }}>Assessment Failed</h4>
          <p style={{ margin: "8px 0 0", color: "#7f1d1d" }}>{(assessmentMutation.error as Error).message}</p>
        </div>
      )}

      {/* Assessment Results */}
      {assessment?.success && assessment.assessment && (
        <AssessmentResults
          assessment={assessment.assessment}
          llmProvider={assessment.llm_provider}
          showReasoning={showReasoning}
          onToggleReasoning={() => setShowReasoning(!showReasoning)}
          reviewState={reviewState}
          isReviewing={isReviewing}
          onStartReview={handleStartReview}
          onToggleDiagnosis={handleToggleDiagnosis}
          onToggleTreatment={handleToggleTreatment}
          onSubmitReview={handleSubmitReview}
          onNotesChange={(notes) => setReviewState(prev => ({ ...prev, physicianNotes: notes }))}
        />
      )}

      {assessment && !assessment.success && (
        <div style={{ ...cardStyle, background: "#fef2f2", border: "1px solid #fecaca" }}>
          <h4 style={{ margin: 0, color: "#dc2626" }}>Assessment Error</h4>
          <p style={{ margin: "8px 0 0", color: "#7f1d1d" }}>{assessment.error}</p>
        </div>
      )}
    </div>
  );
}

// Assessment Results Component
function AssessmentResults({
  assessment,
  llmProvider,
  showReasoning,
  onToggleReasoning,
  reviewState,
  isReviewing,
  onStartReview,
  onToggleDiagnosis,
  onToggleTreatment,
  onSubmitReview,
  onNotesChange,
}: {
  assessment: ClinicalAssessment;
  llmProvider?: string;
  showReasoning: boolean;
  onToggleReasoning: () => void;
  reviewState: ReviewState;
  isReviewing: boolean;
  onStartReview: () => void;
  onToggleDiagnosis: (index: number) => void;
  onToggleTreatment: (index: number) => void;
  onSubmitReview: (status: "approved" | "rejected" | "modified") => void;
  onNotesChange: (notes: string) => void;
}) {
  const cardStyle = { border: "1px solid #eee", borderRadius: 12, padding: 16, marginBottom: 16 };

  const reviewStatusColors = {
    pending: { bg: "#fef3c7", text: "#92400e", label: "Pending Review" },
    approved: { bg: "#dcfce7", text: "#166534", label: "Approved" },
    rejected: { bg: "#fee2e2", text: "#dc2626", label: "Rejected" },
    modified: { bg: "#dbeafe", text: "#1e40af", label: "Modified & Approved" },
  };

  return (
    <div>
      {/* Summary Header */}
      <div style={{ ...cardStyle, background: assessment.requires_human_review ? "#fef3c7" : "#f0fdf4" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 24 }}>{assessment.requires_human_review ? "⚠️" : "✅"}</span>
              <h4 style={{ margin: 0 }}>Assessment Complete</h4>
            </div>
            <div style={{ marginTop: 8, fontSize: 13, color: "#64748b" }}>
              Confidence: <strong>{(assessment.confidence * 100).toFixed(0)}%</strong>
              {llmProvider && <span> • LLM: {llmProvider}</span>}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {reviewState.reviewStatus !== "pending" && (
              <div style={{
                padding: "6px 12px",
                background: reviewStatusColors[reviewState.reviewStatus].bg,
                color: reviewStatusColors[reviewState.reviewStatus].text,
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 600,
              }}>
                {reviewStatusColors[reviewState.reviewStatus].label}
              </div>
            )}
            {assessment.requires_human_review && reviewState.reviewStatus === "pending" && (
              <button
                onClick={onStartReview}
                style={{
                  padding: "8px 16px",
                  background: isReviewing ? "#64748b" : "#059669",
                  color: "white",
                  border: "none",
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {isReviewing ? "Reviewing..." : "Start Review"}
              </button>
            )}
          </div>
        </div>

        {assessment.review_reason && (
          <div style={{ marginTop: 12, padding: 8, background: "#fef9c3", borderRadius: 6, fontSize: 13 }}>
            {assessment.review_reason}
          </div>
        )}

        {assessment.warnings.length > 0 && (
          <div style={{ marginTop: 12 }}>
            {assessment.warnings.map((warning, i) => (
              <div key={i} style={{ padding: 8, background: "#fee2e2", borderRadius: 6, fontSize: 13, color: "#dc2626", marginBottom: 4 }}>
                ⚠️ {warning}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Physician Review Panel */}
      {isReviewing && (
        <div style={{ ...cardStyle, background: "#eff6ff", border: "2px solid #3b82f6" }}>
          <h4 style={{ margin: "0 0 16px", color: "#1e40af", display: "flex", alignItems: "center", gap: 8 }}>
            <span>👨‍⚕️</span> Physician Review
          </h4>

          {/* Review Diagnoses */}
          <div style={{ marginBottom: 16 }}>
            <h5 style={{ margin: "0 0 8px", fontSize: 14 }}>Review Diagnoses</h5>
            {assessment.diagnoses.map((dx, i) => (
              <label
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: 8,
                  background: reviewState.approvedDiagnoses.has(i) ? "#dcfce7" : "#fee2e2",
                  borderRadius: 6,
                  marginBottom: 4,
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={reviewState.approvedDiagnoses.has(i)}
                  onChange={() => onToggleDiagnosis(i)}
                  style={{ width: 18, height: 18 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500 }}>{dx.diagnosis}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    {dx.icd10_code} • Confidence: {(dx.confidence * 100).toFixed(0)}%
                  </div>
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: reviewState.approvedDiagnoses.has(i) ? "#166534" : "#dc2626" }}>
                  {reviewState.approvedDiagnoses.has(i) ? "APPROVED" : "REJECTED"}
                </span>
              </label>
            ))}
          </div>

          {/* Review Treatments */}
          <div style={{ marginBottom: 16 }}>
            <h5 style={{ margin: "0 0 8px", fontSize: 14 }}>Review Treatments</h5>
            {assessment.treatments.map((tx, i) => (
              <label
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: 8,
                  background: reviewState.approvedTreatments.has(i) ? "#dcfce7" : "#fee2e2",
                  borderRadius: 6,
                  marginBottom: 4,
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={reviewState.approvedTreatments.has(i)}
                  onChange={() => onToggleTreatment(i)}
                  style={{ width: 18, height: 18 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500 }}>{tx.description}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    {tx.treatment_type} • Priority: {tx.priority}
                  </div>
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: reviewState.approvedTreatments.has(i) ? "#166534" : "#dc2626" }}>
                  {reviewState.approvedTreatments.has(i) ? "APPROVED" : "REJECTED"}
                </span>
              </label>
            ))}
          </div>

          {/* Physician Notes */}
          <div style={{ marginBottom: 16 }}>
            <h5 style={{ margin: "0 0 8px", fontSize: 14 }}>Physician Notes</h5>
            <textarea
              value={reviewState.physicianNotes}
              onChange={(e) => onNotesChange(e.target.value)}
              placeholder="Add clinical notes, modifications, or additional recommendations..."
              style={{
                width: "100%",
                minHeight: 80,
                padding: 12,
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 13,
                resize: "vertical",
              }}
            />
          </div>

          {/* Submit Buttons */}
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button
              onClick={() => onSubmitReview("rejected")}
              style={{
                padding: "10px 20px",
                background: "#dc2626",
                color: "white",
                border: "none",
                borderRadius: 6,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Reject Assessment
            </button>
            <button
              onClick={() => onSubmitReview("modified")}
              style={{
                padding: "10px 20px",
                background: "#2563eb",
                color: "white",
                border: "none",
                borderRadius: 6,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Approve with Modifications
            </button>
            <button
              onClick={() => onSubmitReview("approved")}
              style={{
                padding: "10px 20px",
                background: "#059669",
                color: "white",
                border: "none",
                borderRadius: 6,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Approve All
            </button>
          </div>
        </div>
      )}

      {/* Critical Findings */}
      {assessment.critical_findings.length > 0 && (
        <div style={{ ...cardStyle, background: "#fef2f2", border: "1px solid #fecaca" }}>
          <h4 style={{ margin: "0 0 12px", color: "#dc2626" }}>Critical Findings</h4>
          {assessment.critical_findings.map((finding, i) => (
            <FindingCard key={i} finding={finding} />
          ))}
        </div>
      )}

      {/* Main Content Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Diagnoses */}
        <div style={cardStyle}>
          <h4 style={{ margin: "0 0 12px", display: "flex", alignItems: "center", gap: 8 }}>
            <span>🩺</span> Diagnoses
            <span style={{ fontSize: 12, color: "#64748b", fontWeight: 400 }}>
              ({assessment.diagnoses.length})
            </span>
          </h4>
          {assessment.diagnoses.length > 0 ? (
            assessment.diagnoses.map((dx, i) => (
              <DiagnosisCard key={i} diagnosis={dx} />
            ))
          ) : (
            <div style={{ color: "#64748b", fontSize: 13 }}>No diagnoses identified</div>
          )}
        </div>

        {/* Treatments */}
        <div style={cardStyle}>
          <h4 style={{ margin: "0 0 12px", display: "flex", alignItems: "center", gap: 8 }}>
            <span>💊</span> Treatment Recommendations
            <span style={{ fontSize: 12, color: "#64748b", fontWeight: 400 }}>
              ({assessment.treatments.length})
            </span>
          </h4>
          {assessment.treatments.length > 0 ? (
            assessment.treatments.map((tx, i) => (
              <TreatmentCard key={i} treatment={tx} />
            ))
          ) : (
            <div style={{ color: "#64748b", fontSize: 13 }}>No specific treatments recommended</div>
          )}
        </div>
      </div>

      {/* Clinical Codes */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* ICD-10 Codes */}
        <div style={cardStyle}>
          <h4 style={{ margin: "0 0 12px" }}>ICD-10 Codes</h4>
          {assessment.icd10_codes.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {assessment.icd10_codes.map((code, i) => (
                <div
                  key={i}
                  style={{
                    padding: "6px 10px",
                    background: "#dbeafe",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  title={code.description}
                >
                  <strong>{code.code}</strong>
                  <span style={{ color: "#64748b", marginLeft: 4 }}>
                    ({(code.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "#64748b", fontSize: 13 }}>No ICD-10 codes suggested</div>
          )}
        </div>

        {/* CPT Codes */}
        <div style={cardStyle}>
          <h4 style={{ margin: "0 0 12px" }}>CPT Codes</h4>
          {assessment.cpt_codes.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {assessment.cpt_codes.map((code, i) => (
                <div
                  key={i}
                  style={{
                    padding: "6px 10px",
                    background: "#dcfce7",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  title={code.description}
                >
                  <strong>{code.code}</strong>
                  <span style={{ color: "#64748b", marginLeft: 4 }}>
                    {code.category}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "#64748b", fontSize: 13 }}>No CPT codes suggested</div>
          )}
        </div>
      </div>

      {/* All Findings */}
      {assessment.findings.length > 0 && (
        <div style={cardStyle}>
          <h4 style={{ margin: "0 0 12px" }}>Clinical Findings ({assessment.findings.length})</h4>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            {assessment.findings.map((finding, i) => (
              <FindingCard key={i} finding={finding} compact />
            ))}
          </div>
        </div>
      )}

      {/* Reasoning Toggle */}
      <div style={cardStyle}>
        <button
          onClick={onToggleReasoning}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: "#0284c7",
            fontWeight: 500,
          }}
        >
          <span>{showReasoning ? "▼" : "▶"}</span>
          Clinical Reasoning ({assessment.reasoning.length} steps)
        </button>

        {showReasoning && (
          <div style={{ marginTop: 12, maxHeight: 400, overflow: "auto" }}>
            {assessment.reasoning.map((step, i) => (
              <div
                key={i}
                style={{
                  padding: 8,
                  background: i % 2 === 0 ? "#f8fafc" : "#fff",
                  borderRadius: 4,
                  fontSize: 13,
                  fontFamily: "monospace",
                  whiteSpace: "pre-wrap",
                }}
              >
                {step}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Finding Card Component
function FindingCard({ finding, compact }: { finding: ClinicalFinding; compact?: boolean }) {
  const statusColors = {
    normal: { bg: "#f0fdf4", border: "#bbf7d0", text: "#166534" },
    abnormal: { bg: "#fef3c7", border: "#fde68a", text: "#92400e" },
    critical: { bg: "#fee2e2", border: "#fecaca", text: "#dc2626" },
  };

  const colors = statusColors[finding.status];

  if (compact) {
    return (
      <div
        style={{
          padding: 8,
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: 6,
          fontSize: 12,
        }}
      >
        <div style={{ fontWeight: 500, color: colors.text }}>{finding.name}</div>
        <div style={{ color: "#64748b" }}>
          {finding.value} {finding.unit}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: 12,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        marginBottom: 8,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontWeight: 600, color: colors.text }}>{finding.name}</div>
          <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>
            {finding.value} {finding.unit}
          </div>
        </div>
        <span
          style={{
            padding: "4px 8px",
            background: colors.text,
            color: "white",
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 600,
            textTransform: "uppercase",
          }}
        >
          {finding.status}
        </span>
      </div>
      <div style={{ marginTop: 8, fontSize: 13, color: "#64748b" }}>{finding.interpretation}</div>
      {finding.reference_range && (
        <div style={{ marginTop: 4, fontSize: 12, color: "#94a3b8" }}>
          Reference: {finding.reference_range}
        </div>
      )}
    </div>
  );
}

// Diagnosis Card Component
function DiagnosisCard({ diagnosis }: { diagnosis: DiagnosisRecommendation }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        padding: 12,
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        marginBottom: 8,
      }}
    >
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", cursor: "pointer" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <div style={{ fontWeight: 600, color: "#1e293b" }}>{diagnosis.diagnosis}</div>
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>
            ICD-10: <strong style={{ color: "#2563eb" }}>{diagnosis.icd10_code}</strong>
            <span style={{ marginLeft: 12 }}>
              Confidence: <strong>{(diagnosis.confidence * 100).toFixed(0)}%</strong>
            </span>
          </div>
        </div>
        <span style={{ color: "#64748b" }}>{expanded ? "▼" : "▶"}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e2e8f0" }}>
          <div style={{ fontSize: 13, color: "#475569", marginBottom: 8 }}>{diagnosis.rationale}</div>

          {diagnosis.differential_diagnoses && diagnosis.differential_diagnoses.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: "#64748b", marginBottom: 4 }}>
                Differential Diagnoses:
              </div>
              {diagnosis.differential_diagnoses.map((diff, i) => (
                <div key={i} style={{ fontSize: 12, color: "#64748b", padding: "4px 0" }}>
                  • {diff.diagnosis} ({diff.icd10}) - {(diff.confidence * 100).toFixed(0)}%
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Treatment Card Component
function TreatmentCard({ treatment }: { treatment: TreatmentRecommendation }) {
  const priorityColors = {
    immediate: { bg: "#fee2e2", text: "#dc2626" },
    urgent: { bg: "#fef3c7", text: "#d97706" },
    routine: { bg: "#dbeafe", text: "#2563eb" },
  };

  const colors = priorityColors[treatment.priority as keyof typeof priorityColors] || priorityColors.routine;

  return (
    <div
      style={{
        padding: 12,
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        marginBottom: 8,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                padding: "2px 6px",
                background: colors.bg,
                color: colors.text,
                borderRadius: 4,
                fontSize: 10,
                fontWeight: 600,
                textTransform: "uppercase",
              }}
            >
              {treatment.priority}
            </span>
            <span style={{ fontSize: 11, color: "#64748b", textTransform: "capitalize" }}>
              {treatment.treatment_type}
            </span>
          </div>
          <div style={{ fontWeight: 500, marginTop: 6, color: "#1e293b" }}>{treatment.description}</div>
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{treatment.rationale}</div>
        </div>
        {treatment.cpt_code && (
          <div style={{ padding: "4px 8px", background: "#dcfce7", borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
            CPT: {treatment.cpt_code}
          </div>
        )}
      </div>

      {treatment.contraindications && treatment.contraindications.length > 0 && (
        <div style={{ marginTop: 8, fontSize: 12, color: "#dc2626" }}>
          ⚠️ Contraindications: {treatment.contraindications.join(", ")}
        </div>
      )}
    </div>
  );
}
