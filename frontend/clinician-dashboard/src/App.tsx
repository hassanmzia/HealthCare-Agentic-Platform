import { useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { TopBar } from "./components/TopBar";
import { PatientPicker } from "./components/PatientPicker";
import { fetchObservations, normalizeVitals } from "./lib/fhirApi";
import { fetchRecommendations } from "./lib/api";
import { VitalsCharts } from "./components/VitalsCharts";
import { RecommendationsPanel } from "./components/RecommendationsPanel";
import { PatientList } from "./components/PatientList";
import { PatientForm } from "./components/PatientForm";
import { PatientImport } from "./components/PatientImport";
import type { Patient } from "./lib/patientApi";

const qc = new QueryClient();

type View = "dashboard" | "patients";

function VitalsDashboard() {
  const [patientRef, setPatientRef] = useState<string>("");

  const obsQ = useQuery({
    queryKey: ["obs", patientRef],
    queryFn: () => fetchObservations({ patientRef: patientRef || undefined, category: "vital-signs", count: 200 }),
    refetchInterval: 15000,
  });

  const rows = useMemo(() => (obsQ.data ? normalizeVitals(obsQ.data) : []), [obsQ.data]);

  const recQ = useQuery({
    queryKey: ["recs", patientRef],
    queryFn: () => fetchRecommendations(patientRef || undefined),
    refetchInterval: 15000,
  });

  return (
    <div style={{ padding: 16, display: "grid", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <PatientPicker patientRef={patientRef} onChange={setPatientRef} />
        <div style={{ display: "flex", gap: 10, fontSize: 12, color: "#666" }}>
          <span>Obs: {obsQ.isFetching ? "refreshing..." : "ready"}</span>
          <span>Recs: {recQ.isFetching ? "refreshing..." : "ready"}</span>
          <button
            onClick={() => {
              obsQ.refetch();
              recQ.refetch();
            }}
            style={{ padding: "7px 10px", borderRadius: 10, border: "1px solid #ddd", background: "#fafafa", cursor: "pointer" }}
          >
            Refresh now
          </button>
        </div>
      </div>

      {obsQ.error ? (
        <div style={{ padding: 12, border: "1px solid #f2dede", background: "#fff2f2", borderRadius: 12 }}>
          <div style={{ fontWeight: 700, color: "#9b1c1c" }}>FHIR query failed</div>
          <div style={{ fontSize: 12, color: "#333" }}>
            Check VITE_FHIR_BASE in .env and confirm the FHIR server is reachable.
          </div>
        </div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ border: "1px solid #eee", borderRadius: 14, padding: 12 }}>
            <div style={{ fontWeight: 700 }}>Vitals Timeline</div>
            <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
              Showing {rows.length} observations (category=vital-signs). Enter a Patient ref to scope results.
            </div>
          </div>

          <VitalsCharts rows={rows} />
        </div>

        <RecommendationsPanel items={recQ.data ?? []} />
      </div>
    </div>
  );
}

function PatientManagement() {
  const [showForm, setShowForm] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    setShowForm(true);
  };

  const handleCreateNew = () => {
    setSelectedPatient(null);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedPatient(null);
  };

  const handleImportSuccess = () => {
    setShowImport(false);
  };

  return (
    <>
      <PatientList
        onSelectPatient={handleSelectPatient}
        onCreateNew={handleCreateNew}
        onImport={() => setShowImport(true)}
      />

      {showForm && (
        <PatientForm
          patient={selectedPatient}
          onClose={() => {
            setShowForm(false);
            setSelectedPatient(null);
          }}
          onSuccess={handleFormSuccess}
        />
      )}

      {showImport && (
        <PatientImport
          onClose={() => setShowImport(false)}
          onSuccess={handleImportSuccess}
        />
      )}
    </>
  );
}

function MainApp() {
  const [currentView, setCurrentView] = useState<View>("dashboard");

  const navButtonStyle = (active: boolean) => ({
    padding: "8px 16px",
    borderRadius: 8,
    border: "none",
    background: active ? "#2563eb" : "transparent",
    color: active ? "white" : "#333",
    cursor: "pointer",
    fontWeight: active ? 600 : 400,
    fontSize: 14,
  });

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif", minHeight: "100vh", background: "#f9fafb" }}>
      <TopBar />

      {/* Navigation */}
      <div style={{ background: "white", borderBottom: "1px solid #eee", padding: "8px 16px" }}>
        <nav style={{ display: "flex", gap: 8 }}>
          <button style={navButtonStyle(currentView === "dashboard")} onClick={() => setCurrentView("dashboard")}>
            Vitals Dashboard
          </button>
          <button style={navButtonStyle(currentView === "patients")} onClick={() => setCurrentView("patients")}>
            Patient Management
          </button>
        </nav>
      </div>

      {/* Content */}
      <main style={{ background: "white", minHeight: "calc(100vh - 120px)" }}>
        {currentView === "dashboard" && <VitalsDashboard />}
        {currentView === "patients" && <PatientManagement />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <MainApp />
    </QueryClientProvider>
  );
}
