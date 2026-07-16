import Link from "next/link";

const FEATURES = [
  { i: "🎯", t: "Cuotas justas del modelo", d: "Cada cuota es 1/probabilidad de un Dixon-Coles calibrado — sin margen de casa oculto." },
  { i: "🧮", t: "Motor estadístico real", d: "Poisson bivariante con corrección de marcadores bajos y decaimiento temporal, validado walk-forward." },
  { i: "🏆", t: "Simulación del torneo", d: "Monte Carlo del Mundial completo: campeón, finalista y avance de grupo." },
  { i: "🔒", t: "Seguro por diseño", d: "Argon2id, JWT rotatorio, RBAC, rate limiting e idempotencia anti doble-apuesta." },
];

export default function Home() {
  return (
    <div className="content-single">
      <section className="hero">
        <span className="chip" style={{ display: "inline-block", marginBottom: 14 }}>Mundial FIFA 2026</span>
        <h1>Predice el Mundial con <span style={{ color: "var(--brand)" }}>cuotas justas</span>, no con la casa a favor.</h1>
        <p>
          Sportsbook académico con <b>puntos virtuales</b>: arma tu boleto, apuesta a 1X2,
          goles y ambos marcan, y compite en el ranking. Todas las cuotas salen de un
          modelo estadístico, no de un margen comercial.
        </p>
        <div className="cta">
          <Link href="/fixtures" className="btn btn-primary">Ver partidos y cuotas →</Link>
          <Link href="/login" className="btn btn-ghost">Crear cuenta · 1000 pts gratis</Link>
        </div>
        <div className="hero-badges">
          <span className="hero-badge"><span className="i">◈</span> 1000 puntos de bienvenida</span>
          <span className="hero-badge"><span className="i">⚡</span> Sin dinero real</span>
          <span className="hero-badge"><span className="i">📈</span> ROI y hit-rate en vivo</span>
        </div>
      </section>

      <div className="section-head"><h2 style={{ margin: 0 }}>¿Qué lo hace distinto?</h2></div>
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
        {FEATURES.map((f) => (
          <div className="card" key={f.t} style={{ textAlign: "left" }}>
            <div style={{ fontSize: "1.6rem", marginBottom: 8 }}>{f.i}</div>
            <div style={{ fontWeight: 800, marginBottom: 4 }}>{f.t}</div>
            <div className="muted small">{f.d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
