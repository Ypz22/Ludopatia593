// Banderas emoji por selección (regional indicators). Fallback a 🏳️.
// Cubre las selecciones que conoce el modelo Dixon-Coles.
const ISO2: Record<string, string> = {
  Argentina: "AR", Australia: "AU", Austria: "AT", Belgium: "BE", Brazil: "BR",
  Cameroon: "CM", Canada: "CA", Chile: "CL", Colombia: "CO", "Costa Rica": "CR",
  Croatia: "HR", "Czech Republic": "CZ", Denmark: "DK", Ecuador: "EC", Egypt: "EG",
  France: "FR", Germany: "DE", Ghana: "GH", Iran: "IR", Italy: "IT", Japan: "JP",
  Mexico: "MX", Morocco: "MA", Netherlands: "NL", Nigeria: "NG", Norway: "NO",
  Panama: "PA", Paraguay: "PY", Peru: "PE", Poland: "PL", Portugal: "PT",
  "Saudi Arabia": "SA", Senegal: "SN", Serbia: "RS", "South Korea": "KR",
  Spain: "ES", Sweden: "SE", Uruguay: "UY", "United States": "US", Switzerland: "CH",
  Turkey: "TR", Ukraine: "UA",
};

// Subdivisiones del Reino Unido usan banderas especiales.
const SPECIAL: Record<string, string> = {
  England: "🏴\u{E0067}\u{E0062}\u{E0065}\u{E006E}\u{E0067}\u{E007F}",
  Scotland: "🏴\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}",
  Wales: "🏴\u{E0067}\u{E0062}\u{E0077}\u{E006C}\u{E0073}\u{E007F}",
};

export function flag(team: string): string {
  if (SPECIAL[team]) return SPECIAL[team];
  const iso = ISO2[team];
  if (!iso) return "🏳️";
  const A = 0x1f1e6;
  return String.fromCodePoint(A + (iso.charCodeAt(0) - 65), A + (iso.charCodeAt(1) - 65));
}

// Nombre corto de la etapa: "group_a" -> "Grupo A", "round_16" -> "Octavos".
export function stageLabel(stage: string): string {
  if (!stage) return "Mundial 2026";
  if (stage.startsWith("group_")) return "Grupo " + stage.split("_")[1].toUpperCase();
  const map: Record<string, string> = {
    round_32: "Dieciseisavos", round_16: "Octavos", quarter: "Cuartos",
    quarter_final: "Cuartos", semi: "Semifinal", semi_final: "Semifinal",
    final: "Final", third_place: "Tercer puesto",
  };
  return map[stage] ?? stage.replace(/_/g, " ");
}
