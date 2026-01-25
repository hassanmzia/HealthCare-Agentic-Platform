import { useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { PatientPicker } from "./components/PatientPicker";
import { fetchObservations, normalizeVitals } from "./lib/fhirApi";
import { fetchRecommendations } from "./lib/api";
import { VitalsCharts } from "./components/VitalsCharts";
import { RecommendationsPanel } from "./components/RecommendationsPanel";
import { PatientList } from "./components/PatientList";
import { PatientForm } from "./components/PatientForm";
import { PatientImport } from "./components/PatientImport";
import { DeviceList } from "./components/DeviceList";
import { DeviceForm } from "./components/DeviceForm";
import { DeviceAssignment } from "./components/DeviceAssignment";
import { SimulatorControl } from "./components/SimulatorControl";
import { DoctorPortal } from "./components/DoctorPortal";
import { AlertsDashboard } from "./components/AlertsDashboard";
import { AnalyticsDashboard } from "./components/AnalyticsDashboard";
import { UserManagement } from "./components/UserManagement";
import { LabsDashboard } from "./components/LabsDashboard";
import { MedicationsDashboard } from "./components/MedicationsDashboard";
import { LoginPage } from "./components/LoginPage";
import { AuthProvider, useAuth } from "./context/AuthContext";
import type { Patient } from "./lib/patientApi";
import type { Device } from "./lib/deviceApi";

const qc = new QueryClient();

type View = "dashboard" | "patients" | "devices" | "simulator" | "doctor" | "labs" | "medications" | "alerts" | "analytics" | "users";

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

function DeviceManagement() {
  const [showForm, setShowForm] = useState(false);
  const [showAssign, setShowAssign] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [deviceToAssign, setDeviceToAssign] = useState<Device | null>(null);

  const handleSelectDevice = (device: Device) => {
    setSelectedDevice(device);
    setShowForm(true);
  };

  const handleCreateNew = () => {
    setSelectedDevice(null);
    setShowForm(true);
  };

  const handleAssign = (device: Device) => {
    setDeviceToAssign(device);
    setShowAssign(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedDevice(null);
  };

  const handleAssignSuccess = () => {
    setShowAssign(false);
    setDeviceToAssign(null);
  };

  return (
    <>
      <DeviceList
        onSelectDevice={handleSelectDevice}
        onCreateNew={handleCreateNew}
        onAssign={handleAssign}
      />

      {showForm && (
        <DeviceForm
          device={selectedDevice}
          onClose={() => {
            setShowForm(false);
            setSelectedDevice(null);
          }}
          onSuccess={handleFormSuccess}
        />
      )}

      {showAssign && deviceToAssign && (
        <DeviceAssignment
          device={deviceToAssign}
          onClose={() => {
            setShowAssign(false);
            setDeviceToAssign(null);
          }}
          onSuccess={handleAssignSuccess}
        />
      )}
    </>
  );
}

function AuthenticatedApp() {
  const { user, permissions, logout, isLoading } = useAuth();
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

  if (isLoading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div>Loading...</div>
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif", minHeight: "100vh", background: "#f9fafb" }}>
      {/* Header with user info */}
      <div style={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", color: "white", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 32, height: 32, background: "rgba(255,255,255,0.2)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700 }}>
            +
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Health Platform</div>
            <div style={{ fontSize: 11, opacity: 0.8 }}>Clinical Dashboard</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{user?.display_name}</div>
            <div style={{ fontSize: 11, opacity: 0.8 }}>{user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : ""} {user?.department ? `- ${user.department}` : ""}</div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: "6px 12px",
              background: "rgba(255,255,255,0.2)",
              border: "1px solid rgba(255,255,255,0.3)",
              borderRadius: 6,
              color: "white",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div style={{ background: "white", borderBottom: "1px solid #eee", padding: "8px 16px" }}>
        <nav style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button style={navButtonStyle(currentView === "dashboard")} onClick={() => setCurrentView("dashboard")}>
            Vitals Dashboard
          </button>
          {permissions?.can_view_patients && (
            <button style={navButtonStyle(currentView === "patients")} onClick={() => setCurrentView("patients")}>
              Patients
            </button>
          )}
          <button style={navButtonStyle(currentView === "devices")} onClick={() => setCurrentView("devices")}>
            Devices
          </button>
          {permissions?.can_manage_devices && (
            <button style={navButtonStyle(currentView === "simulator")} onClick={() => setCurrentView("simulator")}>
              IoT Simulator
            </button>
          )}
          {permissions?.can_view_clinical_data && (
            <button style={navButtonStyle(currentView === "doctor")} onClick={() => setCurrentView("doctor")}>
              Doctor Portal
            </button>
          )}
          {permissions?.can_view_clinical_data && (
            <button style={navButtonStyle(currentView === "labs")} onClick={() => setCurrentView("labs")}>
              Labs
            </button>
          )}
          {permissions?.can_view_clinical_data && (
            <button style={navButtonStyle(currentView === "medications")} onClick={() => setCurrentView("medications")}>
              Medications
            </button>
          )}
          {permissions?.can_manage_alerts && (
            <button style={navButtonStyle(currentView === "alerts")} onClick={() => setCurrentView("alerts")}>
              Alerts
            </button>
          )}
          {permissions?.can_view_analytics && (
            <button style={navButtonStyle(currentView === "analytics")} onClick={() => setCurrentView("analytics")}>
              Analytics
            </button>
          )}
          {permissions?.can_manage_users && (
            <button style={navButtonStyle(currentView === "users")} onClick={() => setCurrentView("users")}>
              Users
            </button>
          )}
        </nav>
      </div>

      {/* Content */}
      <main style={{ background: "white", minHeight: "calc(100vh - 140px)" }}>
        {currentView === "dashboard" && <VitalsDashboard />}
        {currentView === "patients" && <PatientManagement />}
        {currentView === "devices" && <DeviceManagement />}
        {currentView === "simulator" && <SimulatorControl />}
        {currentView === "doctor" && <DoctorPortal />}
        {currentView === "labs" && <LabsDashboard />}
        {currentView === "medications" && <MedicationsDashboard />}
        {currentView === "alerts" && <AlertsDashboard />}
        {currentView === "analytics" && <AnalyticsDashboard />}
        {currentView === "users" && <UserManagement />}
      </main>
    </div>
  );
}

function MainApp() {
  const { isAuthenticated, isLoading } = useAuth();
  const [, setForceRender] = useState(0);

  if (isLoading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "system-ui" }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setForceRender((n) => n + 1)} />;
  }

  return <AuthenticatedApp />;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </QueryClientProvider>
  );
}
