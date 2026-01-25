import { useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { TopBar } from "./components/TopBar";
import { PatientPicker } from "./components/PatientPicker";
import { fetchObservations, normalizeVitals } from "./lib/fhirApi";
import { fetchRecommendations } from "./lib/api";
import { VitalsCharts } from "./components/VitalsCharts";
import { RecommendationsPanel } from "./components/RecommendationsPanel";

const qc = new QueryClient();

function Dashboard() {
  const [patientRef, setPatientRef] = useState<string>("");

  const obsQ = useQuery({
    queryKey: ["obs", patientRef],
    queryFn: () => fetchObservations({ patientRef: patientRef || undefined, category: "vital-signs", count: 200 }),
    refetchInterval: 15000, // refresh every 15s
  });

  const rows = useMemo(() => (obsQ.data ? normalizeVitals(obsQ.data) : []), [obsQ.data]);

  // Map a patientId to your Django layer if you have it; for now, use patientRef string
  const recQ = useQuery({
    queryKey: ["recs", patientRef],
    queryFn: () => fetchRecommendations(patientRef || undefined),
    refetchInterval: 15000,
  });

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif" }}>
      <TopBar />

      <div style={{ padding: 16, display: "grid", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <PatientPicker patientRef={patientRef} onChange={setPatientRef} />
          <div style={{ display: "flex", gap: 10, fontSize: 12, color: "#666" }}>
            <span>Obs: {obsQ.isFetching ? "refreshing…" : "ready"}</span>
            <span>Recs: {recQ.isFetching ? "refreshing…" : "ready"}</span>
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
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Dashboard />
    </QueryClientProvider>
  );
}

