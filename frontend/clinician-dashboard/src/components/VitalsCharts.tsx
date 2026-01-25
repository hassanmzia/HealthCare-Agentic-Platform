import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

type Row = {
  time: string;
  name: string;
  loinc: string;
  value: number | null;
  unit: string;
  bp_sys: number | null;
  bp_dia: number | null;
};

function compactTime(t: string) {
  if (!t) return "";
  // keep it simple; ISO substring
  return t.replace("T", " ").replace("Z", "").slice(0, 16);
}

export function VitalsCharts({ rows }: { rows: Row[] }) {
  // Separate series by LOINC (and BP by sys/dia)
  const hr = rows.filter(r => r.loinc === "8867-4" && r.value != null).map(r => ({ t: compactTime(r.time), v: r.value }));
  const rr = rows.filter(r => r.loinc === "9279-1" && r.value != null).map(r => ({ t: compactTime(r.time), v: r.value }));
  const spo2 = rows.filter(r => r.loinc === "59408-5" && r.value != null).map(r => ({ t: compactTime(r.time), v: r.value }));
  const temp = rows.filter(r => r.loinc === "8310-5" && r.value != null).map(r => ({ t: compactTime(r.time), v: r.value }));
  const weight = rows.filter(r => r.loinc === "29463-7" && r.value != null).map(r => ({ t: compactTime(r.time), v: r.value }));
  const bp = rows
    .filter(r => r.bp_sys != null || r.bp_dia != null)
    .map(r => ({ t: compactTime(r.time), sys: r.bp_sys, dia: r.bp_dia }));

  const Card = ({ title, children }: { title: string; children: any }) => (
    <div style={{ border: "1px solid #eee", borderRadius: 14, padding: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div style={{ height: 220 }}>{children}</div>
    </div>
  );

  const SimpleLine = ({ data, dataKey, name }: { data: any[]; dataKey: string; name: string }) => (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey={dataKey} name={name} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
      <Card title="Heart Rate (HR)">
        <SimpleLine data={hr} dataKey="v" name="bpm" />
      </Card>
      <Card title="Respiratory Rate (RR)">
        <SimpleLine data={rr} dataKey="v" name="breaths/min" />
      </Card>
      <Card title="SpO₂">
        <SimpleLine data={spo2} dataKey="v" name="%" />
      </Card>
      <Card title="Temperature">
        <SimpleLine data={temp} dataKey="v" name="°C" />
      </Card>
      <Card title="Weight">
        <SimpleLine data={weight} dataKey="v" name="kg" />
      </Card>
      <Card title="Blood Pressure (SYS/DIA)">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={bp}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="sys" name="SYS" dot={false} />
            <Line type="monotone" dataKey="dia" name="DIA" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

