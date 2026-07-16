"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      if (mode === "register") await api.register(email, password);
      await api.login(email, password);
      window.dispatchEvent(new Event("balance:refresh"));
      router.push("/fixtures");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="content-single auth-wrap">
      <div className="card auth-card">
        <div className="brand" style={{ justifyContent: "center", margin: "0 0 18px", fontSize: "1.2rem" }}>
          <span className="logo">⚽</span>
          <span>Predictor<span className="accent">26</span></span>
        </div>

        <div className="auth-tabs">
          <button className={`auth-tab ${mode === "login" ? "active" : ""}`}
            onClick={() => { setMode("login"); setErr(""); }}>Iniciar sesión</button>
          <button className={`auth-tab ${mode === "register" ? "active" : ""}`}
            onClick={() => { setMode("register"); setErr(""); }}>Crear cuenta</button>
        </div>

        <form onSubmit={submit}>
          <label>Correo electrónico</label>
          <input type="email" placeholder="tu@correo.com" value={email}
            onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />

          <label>Contraseña {mode === "register" && <span className="muted">· mín. 10 caracteres</span>}</label>
          <input type="password" placeholder="••••••••••" value={password}
            onChange={(e) => setPassword(e.target.value)} required
            minLength={mode === "register" ? 10 : 1} autoComplete={mode === "register" ? "new-password" : "current-password"} />

          {err && <p className="err" style={{ marginTop: 12 }}>⚠ {err}</p>}

          <button className="btn btn-primary btn-block" disabled={busy} type="submit" style={{ marginTop: 18 }}>
            {busy ? <span className="spinner" /> : mode === "login" ? "Entrar" : "Crear cuenta y jugar"}
          </button>
        </form>

        <div className="divider" />
        <div className="auth-perk"><span className="i">◈</span> Recibes <b>&nbsp;1000 puntos&nbsp;</b> virtuales al registrarte.</div>
        <div className="auth-perk"><span className="i">🔒</span> Contraseñas con Argon2id · sesiones JWT rotatorias.</div>
        <div className="auth-perk"><span className="i">🎯</span> Cuotas justas sin margen de casa (modelo Dixon-Coles).</div>
      </div>
      <p className="muted tiny" style={{ textAlign: "center", marginTop: 14 }}>
        Puntos virtuales sin valor monetario · proyecto académico de software seguro.
      </p>
    </div>
  );
}
