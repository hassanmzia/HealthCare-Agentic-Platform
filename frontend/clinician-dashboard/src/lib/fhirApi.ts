import { fhir } from "./http";
import type { FhirBundle, Observation } from "./fhirTypes";

export async function fetchObservations(params: {
  patientRef?: string;        // e.g. "Patient/123" or just "123"
  count?: number;             // default 100
  category?: string;          // "vital-signs"
}) {
  const count = params.count ?? 100;
  const q: Record<string, string> = { _count: String(count) };

  if (params.category) q["category"] = params.category;
  if (params.patientRef) {
    // Support both "Patient/123" format and just "123"
    const ref = params.patientRef.includes("/")
      ? params.patientRef
      : `Patient/${params.patientRef}`;
    q["subject"] = ref;
  }

  const search = new URLSearchParams(q).toString();
  const res = await fhir.get<FhirBundle<Observation>>(`/Observation?${search}`);
  return res.data;
}

export function normalizeVitals(bundle: FhirBundle<Observation>) {
  const entries = bundle.entry?.map(e => e.resource).filter(Boolean) ?? [];

  // Extract key vitals + BP components into a common row structure for charts
  const rows = entries.map(o => {
    const code = o.code?.coding?.[0]?.code ?? "";
    const display = o.code?.coding?.[0]?.display ?? "Observation";
    const t = o.effectiveDateTime ?? o.issued ?? "";

    // BP special handling (component systolic/diastolic)
    const sys = o.component?.find(c => c.code?.coding?.[0]?.code === "8480-6")?.valueQuantity?.value;
    const dia = o.component?.find(c => c.code?.coding?.[0]?.code === "8462-4")?.valueQuantity?.value;

    return {
      id: o.id ?? "",
      time: t,
      loinc: code,
      name: display,
      value: o.valueQuantity?.value ?? null,
      unit: o.valueQuantity?.unit ?? "",
      bp_sys: sys ?? null,
      bp_dia: dia ?? null,
    };
  });

  // Sort ascending by time for charts
  rows.sort((a, b) => (a.time || "").localeCompare(b.time || ""));
  return rows;
}

