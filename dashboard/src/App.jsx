import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import ReactFlow, {
  Background,
  Controls
} from "reactflow";

import "reactflow/dist/style.css";
export default function App() {
  const [timeline, setTimeline] = useState([]);
  const [logs, setLogs] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const serviceRiskMap = {};

  useEffect(() => {

  const fetchTimeline = async () => {

    const res = await fetch(
      "http://localhost:5500/timeline"
    );

    const data = await res.json();
    console.log(data);
    setTimeline(data.reverse());

  };

  fetchTimeline();

  const interval = setInterval(
    fetchTimeline,
    4000
  );

  return () => clearInterval(interval);

}, []);
  logs.forEach((log) => {
    serviceRiskMap[log.service] = log.risk;
  });
  const getNodeColor = (risk) => {

  if (risk > 0.7) return "#ef4444";

  if (risk > 0.4) return "#facc15";

  return "#22c55e";
};

const nodes = [

  {
    id: "auth",
    position: { x: 100, y: 100 },
    data: { label: "Auth Service" },
    style: {
      background: getNodeColor(serviceRiskMap["auth"] || 0),
      color: "white",
      padding: 10,
      borderRadius: 10
    }
  },

  {
    id: "payment",
    position: { x: 100, y: 250 },
    data: { label: "Payment Service" },
    style: {
      background: getNodeColor(serviceRiskMap["payment"] || 0),
      color: "white",
      padding: 10,
      borderRadius: 10
    }
  },

  {
    id: "search",
    position: { x: 100, y: 400 },
    data: { label: "Search Service" },
    style: {
      background: getNodeColor(serviceRiskMap["search"] || 0),
      color: "white",
      padding: 10,
      borderRadius: 10
    }
  },

  {
    id: "database",
    position: { x: 500, y: 250 },
    data: { label: "Database" },
    style: {
      background: getNodeColor(serviceRiskMap["database"] || 0),
      color: "white",
      padding: 10,
      borderRadius: 10
    }
  }

];
const edges = [

  {
    id: "e1",
    source: "auth",
    target: "database",
    animated: true
  },

  {
    id: "e2",
    source: "payment",
    target: "database",
    animated: true
  },

  {
    id: "e3",
    source: "search",
    target: "database",
    animated: true
  }

];
  // -------------------------
  // WEBSOCKET LIVE DATA
  // -------------------------
  useEffect(() => {

    const socket = new WebSocket("ws://localhost:8765");

    socket.onmessage = (event) => {

      const data = JSON.parse(event.data);
      console.log(data);
      setLogs((prev) => [...prev.slice(-15), data]);

    };

    return () => socket.close();

  }, []);

  // -------------------------
  // FETCH INCIDENTS
  // -------------------------
  useEffect(() => {

    const fetchIncidents = async () => {

      const res = await fetch("http://localhost:5500/incidents");

      const data = await res.json();

      setIncidents(data);

    };

    fetchIncidents();

    const interval = setInterval(fetchIncidents, 5000);

    return () => clearInterval(interval);

  }, []);

  return (
    <div className="min-h-screen p-6 bg-slate-900 text-white">

      <h1 className="text-4xl font-bold mb-6">
        🚀 AI Infrastructure Monitoring Dashboard
      </h1>

      {/* LIVE STATUS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">

        <Card title="Auth API" status="Healthy" />
        <Card title="Payment API" status="Warning" />
        <Card title="Search API" status="Healthy" />
        <Card title="Database API" status="Critical" />

      </div>

      {/* LIVE LATENCY CHART */}
      <div className="bg-slate-800 p-4 rounded-2xl mb-8">

        <h2 className="text-2xl mb-4">
          📈 Live Latency
        </h2>

        <ResponsiveContainer width="100%" height={300}>

          <LineChart data={logs}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="time" />

            <YAxis />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="latency"
              stroke="#38bdf8"
            />

          </LineChart>

        </ResponsiveContainer>

      </div>
      {/* TOPOLOGY VISUALIZATION */}
<div className="bg-slate-800 p-4 rounded-2xl mb-8">

  <h2 className="text-2xl mb-4">
    🌐 Infrastructure Topology
  </h2>

  <div style={{ width: "100%", height: "500px" }}>

    <ReactFlow
      nodes={nodes}
      edges={edges}
      fitView
    >

      <Background />

      <Controls />

    </ReactFlow>

  </div>

</div>

      {/* LIVE PREDICTIONS */}
      <div className="bg-slate-800 p-4 rounded-2xl">

        <h2 className="text-2xl mb-4">
          🧠 Live Predictions
        </h2>

        <div className="space-y-3">

          {logs.slice().reverse().map((log, index) => (

            <div
              key={index}
              className="bg-slate-700 p-4 rounded-xl"
            >

              <div className="flex justify-between mb-2">

                <div>
                  <strong>{log.service}</strong>
                </div>

                <div>
                  Latency: {log.latency}ms
                </div>

                <div>
                  CPU: {log.cpu}%
                </div>

                <div>
                  <strong>Risk:</strong>
                  <div>

                      Health Score:

                      <span
                        className={
                          log.health_score < 50
                            ? "text-red-400 ml-2"
                            : log.health_score < 75
                            ? "text-yellow-400 ml-2"
                            : "text-green-400 ml-2"
                        }
                      >

                        {log.health_score}/100

                      </span>

                    </div>
                    <div>

                        Status:

                        <span
                          className={
                            log.health_score < 50
                              ? "text-red-400 ml-2"
                              : log.health_score < 75
                              ? "text-yellow-400 ml-2"
                              : "text-green-400 ml-2"
                          }
                        >

                          {
                            log.health_score < 50
                              ? "Critical"
                              : log.health_score < 75
                              ? "Warning"
                              : "Healthy"
                          }

                        </span>

                      </div>
                  <span
                    className={
                      log.risk > 0.7
                        ? "text-red-400 ml-2"
                        : "text-green-400 ml-2"
                    }
                  >
                    {(log.risk * 100).toFixed(1)}%
                  </span>

                </div>
<div className="w-full bg-slate-600 rounded-full h-3 mt-2">

  <div
    className={`h-3 rounded-full ${
      log.risk > 0.7
        ? "bg-red-500"
        : log.risk > 0.4
        ? "bg-yellow-400"
        : "bg-green-500"
    }`}
    style={{
      width: `${log.risk * 100}%`
    }}
  />

</div>
              </div>

              {/* ROOT CAUSE AI */}
              <div className="mt-2 text-sm text-slate-300">

                <strong>Causes:</strong>

                <ul className="list-disc ml-5 mt-1">

                  {log.causes?.map((cause, i) => (

                    <li key={i}>
                      {cause}
                    </li>

                  ))}

                </ul>

              </div>
{/* SHAP EXPLAINABLE AI */}

<div className="mt-3 text-sm text-cyan-300">

  <strong>AI Explanation:</strong>

  <ul className="list-disc ml-5 mt-1">

    {log.explanations?.map((item, i) => (

      <li key={i}>
        {item.feature}: {item.impact}
      </li>

    ))}

  </ul>

</div>

{/* DEPENDENCY INTELLIGENCE */}

<div className="mt-3 text-sm text-yellow-300">

  <strong>Dependencies:</strong>

  <div className="mt-1">

    {
      log.dependencies?.length > 0
        ? log.dependencies.join(", ")
        : "No dependencies"
    }

  </div>

</div>

{/* CASCADE FAILURE */}

{
  log.cascade_impacts?.length > 0 && (

    <div className="mt-3">

      <strong className="text-red-400">

        Cascade Risk:

      </strong>

      <div className="mt-1 text-red-300">

        Failure may spread to:

        {
          log.cascade_impacts.join(", ")
        }

      </div>

    </div>

  )
}

{/* SELF HEALING ENGINE */}

<div className="mt-3 text-sm text-green-300">

  <strong>Self-Healing Actions:</strong>

  <ul className="list-disc ml-5 mt-1">

    {log.healing?.actions?.map((action, i) => (

      <li key={i}>
        {action}
      </li>

    ))}

  </ul>

</div>

{/* SLA / SLO STATUS */}

<div className="mt-3">

  <strong>

    SLA / SLO Status:

  </strong>

  <span
    className={
      log.slo?.status === "VIOLATED"
        ? "text-red-400 ml-2"
        : "text-green-400 ml-2"
    }
  >

    {log.slo?.status}

  </span>

</div>

{
  log.slo?.violations?.length > 0 && (

    <div className="mt-2 text-red-300">

      {
        log.slo.violations.map(
          (item, i) => (

            <div key={i}>
              • {item}
            </div>

          )
        )
      }

    </div>

  )
}
{/* AI FORECASTING */}

<div className="mt-3">

  <strong>
    Forecast:
  </strong>
{/* INCIDENT CORRELATION */}

<div className="mt-3">

  <strong className="text-pink-400">

    Incident Correlation:

  </strong>

</div>
<div className="mt-2 text-sm text-pink-300">

  {

    log.correlation?.root_cause

  }

</div>
<div className="text-sm text-slate-300 mt-1">

  {

    log.correlation?.summary

  }

</div>
{
  log.correlation?.related_services?.length > 0 && (

    <div className="mt-2 text-sm text-orange-300">

      Related Services:

      {

        log.correlation.related_services.join(", ")

      }

    </div>

  )
}
  <span
    className={
      log.forecast?.status ===
      "FAILURE LIKELY"

        ? "text-red-400 ml-2"

        : log.forecast?.status ===
          "UNSTABLE"

        ? "text-yellow-400 ml-2"

        : "text-green-400 ml-2"
    }
  >

    {log.forecast?.status}

  </span>

</div>

<div className="mt-2 text-sm text-slate-300">

  {log.forecast?.message}

</div>

<div className="text-sm text-cyan-300">

  Confidence:
  {log.forecast?.confidence}%

</div>

{/* END OF SINGLE LOG CARD */}

            </div>

          ))}
          

        </div>

      </div>
{/* AI ANOMALY HEATMAP */}

<div className="bg-slate-800 p-4 rounded-2xl mb-8">

  <h2 className="text-2xl mb-4">
    🔥 AI Anomaly Heatmap
  </h2>

  <div className="space-y-2">

    {logs.slice().reverse().map((log, index) => (

      <div
        key={index}
        className="flex items-center gap-4"
      >

        <div className="w-24 text-sm text-slate-400">

          {log.time}

        </div>

        <div className="w-32">

          {log.service}

        </div>

        <div
          className={`h-6 rounded-lg flex-1 transition-all duration-500

            ${
              log.risk > 0.85
                ? "bg-red-500"

                : log.risk > 0.65
                ? "bg-orange-400"

                : log.risk > 0.45
                ? "bg-yellow-400"

                : "bg-green-500"
            }
          `}
        >

        </div>

        <div className="w-20 text-right">

          {(log.risk * 100).toFixed(0)}%

        </div>

      </div>

    ))}

  </div>

</div>
      {/* INCIDENT TIMELINE */}
      <div className="bg-slate-800 p-4 rounded-2xl mt-8">

        <h2 className="text-2xl mb-4">
          🚨 Incident Timeline
        </h2>

        <div className="space-y-3">

          {incidents.map((incident, index) => (

            <div
              key={index}
              className="bg-slate-700 p-4 rounded-xl"
            >

              <div>
                <strong>{incident.service}</strong>
              </div>

              <div className="mt-1">
                Risk: {incident.risk}
              </div>

              <div className="text-sm text-slate-300 mt-1">
                {incident.causes}
              </div>

              <div className="text-xs text-slate-400 mt-2">
                {incident.timestamp}
              </div>

            </div>

          ))}

        </div>

      </div>

    {/* AI INCIDENT REPLAY */}
<div className="bg-slate-800 p-4 rounded-2xl mt-8">

  <h2 className="text-2xl mb-4">
    ⏪ AI Incident Replay
  </h2>

  <div className="space-y-3">

    {timeline.map((event, index) => (

      <div
        key={index}
        className="bg-slate-700 p-4 rounded-xl"
      >

        <div className="flex justify-between">

          <div>
            <strong>
              {event.service}
            </strong>
          </div>

          <div>
            Risk:
            {(event.risk * 100).toFixed(0)}%
          </div>

        </div>

        <div className="mt-2">
          Latency: {event.latency}ms
        </div>

        <div>
          CPU: {event.cpu}%
        </div>

        <div className="mt-2 text-red-400">

          {event.causes?.join(", ")}

        </div>

        <div className="mt-2 text-green-400">

          {event.healing?.actions?.join(", ")}

        </div>

        <div className="mt-2 text-xs text-slate-400">

          {event.time}

        </div>

      </div>

    ))}

  </div>

</div>
</div>
  );
}

// -------------------------
// CARD COMPONENT
// -------------------------
function Card({ title, status }) {

  let color = "text-green-400";

  if (status === "Warning") {
    color = "text-yellow-400";
  }

  if (status === "Critical") {
    color = "text-red-400";
  }

  return (

    <div className="bg-slate-800 p-5 rounded-2xl shadow-lg">

      <h2 className="text-xl mb-2">
        {title}
      </h2>

      <p className={`text-lg font-bold ${color}`}>
        {status}
      </p>

    </div>

  );
}