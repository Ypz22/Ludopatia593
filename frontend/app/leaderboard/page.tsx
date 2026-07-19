"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function LeaderboardPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.leaderboard().then(setRows).catch((e) => setErr(e.message)).finally(() => setLoading(false));
  }, []);

  return (
    <div className="content-single">
      <div className="section-head">
        <h1 style={{ margin: 0 }}>Ranking global</h1>
        <span className="chip">Top 50 por saldo</span>
      </div>

      {err && <div className="card"><p className="err">⚠ {err}</p></div>}

      <div className="card" style={{ padding: 0, overflowX: "auto" }}>
        {loading ? (
          <div style={{ padding: 20 }}><span className="skeleton" style={{ display: "block", height: 160 }} /></div>
        ) : (
          <table>
            <thead>
              <tr><th>#</th><th>Jugador</th><th style={{ textAlign: "right" }}>Puntos</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.user_id}>
                  <td><span className={`rank-badge ${r.rank <= 3 ? "g" + r.rank : ""}`}>{r.rank}</span></td>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 9 }}>
                      <span style={{ width: 26, height: 26, borderRadius: "50%", background: "var(--elev)", display: "grid", placeItems: "center", fontSize: "0.8rem" }}>
                        {r.name?.[0]?.toUpperCase() ?? "?"}
                      </span>
                      <b>{r.name}</b>
                    </span>
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 800, color: "var(--gold)" }}>◈ {r.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
