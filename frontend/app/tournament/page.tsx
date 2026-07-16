"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { flag } from "@/lib/flags";

export default function TournamentPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => { api.tournament().then(setData).catch((e) => setErr(e.message)); }, []);

  return (
    <div className="content-single">
      <div className="section-head">
        <h1 style={{ margin: 0 }}>Ganador del Mundial</h1>
        <span className="chip">Outright · Monte Carlo</span>
      </div>

      {err && <div className="card"><p className="err">⚠ {err}</p>
        <p className="muted small">Se necesitan grupos oficiales cargados para simular el torneo.</p></div>}

      {!data && !err && (
        <div className="card">
          <p className="muted"><span className="spinner" style={{ borderTopColor: "var(--brand)" }} /> Simulando el torneo (Monte Carlo)…</p>
        </div>
      )}

      {data && (() => {
        const champ = (Object.entries(data.champion) as [string, number][]).sort((a, b) => b[1] - a[1]);
        const max = champ.length ? champ[0][1] : 1;
        return (
          <>
            <p className="muted small" style={{ margin: "-8px 2px 16px" }}>
              {data.n_sims?.toLocaleString()} simulaciones · fuente {data.source ?? "demo"} · {data.group_count ?? 0} grupos.
              La cuota es la <b>cuota justa</b> (1 / probabilidad).
            </p>
            <div className="card" style={{ padding: 0, overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>#</th><th>Selección</th><th>Campeón</th>
                    <th>Cuota</th><th>Finalista</th><th>Avanza grupo</th>
                  </tr>
                </thead>
                <tbody>
                  {champ.slice(0, 20).map(([team, p], i) => (
                    <tr key={team}>
                      <td><span className={`rank-badge ${i < 3 ? "g" + (i + 1) : ""}`}>{i + 1}</span></td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                          <span style={{ fontSize: "1.25rem" }}>{flag(team)}</span>
                          <b>{team}</b>
                        </div>
                      </td>
                      <td style={{ minWidth: 150 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <div style={{ flex: 1, height: 6, background: "var(--elev)", borderRadius: 999, overflow: "hidden", minWidth: 60 }}>
                            <div style={{ width: `${(p / max) * 100}%`, height: "100%", background: "linear-gradient(90deg, var(--brand), #0fb87d)" }} />
                          </div>
                          <span style={{ fontWeight: 700, minWidth: 44, textAlign: "right" }}>{(p * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td style={{ fontWeight: 700, color: "var(--brand)" }}>{p > 0 ? (1 / p).toFixed(2) : "—"}</td>
                      <td className="muted">{(((data.finalist[team] ?? 0) as number) * 100).toFixed(1)}%</td>
                      <td className="muted">{(((data.advance_group[team] ?? 0) as number) * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        );
      })()}
    </div>
  );
}
