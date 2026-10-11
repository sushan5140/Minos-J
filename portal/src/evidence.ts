/** E1: Strict, read-only provenance contract. No experimental runner imports. */
export type EvidenceKind = "historical_synthetic_experiment" | "historical_record" | "reproduced_measurement" | "synthetic_ui_demo";
export type Verification = "recovered_and_cross_checked" | "independently_reproduced" | "reported_only" | "unverified";
export type Verdict = "falsified_in_tested_setup" | "structural_pattern_in_tested_setup" | "inconclusive" | "interrupted" | "blocked" | "no_scientific_verdict";
export type TraceEvent = {
  event_id: string;
  stage: string;
  source_path: string;
  observed_at?: string; // never infer from array index
  hypothesis_id?: string;
  transition_from?: string;
  content_summary?: string; // observed summary only; not synthesized thoughts
};
export type Provenance = {
  evidence_kind: EvidenceKind;
  verification: Verification;
  repository: "sushan5140/Minos-J";
  source_path: string;
  protocol_version?: string;
  commit_sha?: string;
};
export type Usage = {
  input_tokens: number | null;
  output_tokens: number | null;
  cached_input_tokens: number | null;
  reported_total_tokens: number | null;
  counting_basis: string;
};
export type ResearchCase = {
  schema_version: 1;
  experiment_id: string;
  case_id: string;
  arm_id?: string;
  verdict: Verdict;
  provenance: Provenance;
  trace_status: "verified_events" | "unavailable";
  trace_events: TraceEvent[];
  model_identity_status: "verified_by_returned_identity" | "requested_only" | "unknown";
  usage?: Usage;
  final_answer?: string;
  ground_truth_status?: "observed" | "unknown";
  scoring_method?: string;
};

const kinds = new Set<EvidenceKind>(["historical_synthetic_experiment","historical_record","reproduced_measurement","synthetic_ui_demo"]);
const verifications = new Set<Verification>(["recovered_and_cross_checked","independently_reproduced","reported_only","unverified"]);
const verdicts = new Set<Verdict>(["falsified_in_tested_setup","structural_pattern_in_tested_setup","inconclusive","interrupted","blocked","no_scientific_verdict"]);
const idStatuses = new Set(["verified_by_returned_identity","requested_only","unknown"]);
const isObject = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const string = (v: unknown) => typeof v === "string" && v.trim().length > 0;
function checkUsage(raw: unknown): void {
  if (!isObject(raw) || !string(raw.counting_basis)) throw new Error("Invalid usage basis");
  for (const k of ["input_tokens","output_tokens","cached_input_tokens","reported_total_tokens"]) {
    const v = raw[k];
    if (v !== null && (typeof v !== "number" || !Number.isSafeInteger(v) || v < 0)) throw new Error("Invalid usage field: " + k);
  }
}
export function parseResearchCase(value: unknown): ResearchCase {
  if (!isObject(value)) throw new Error("Case must be an object");
  if (value.schema_version !== 1 || !string(value.experiment_id) || !string(value.case_id) || !verdicts.has(value.verdict as Verdict))
    throw new Error("Invalid case header");
  if (!isObject(value.provenance)) throw new Error("Missing provenance");
  const p = value.provenance;
  if (!kinds.has(p.evidence_kind as EvidenceKind) || !verifications.has(p.verification as Verification) ||
      p.repository !== "sushan5140/Minos-J" || !string(p.source_path) ||
      (p.commit_sha !== undefined && !/^[a-f0-9]{40}$/.test(String(p.commit_sha))))
    throw new Error("Invalid provenance");
  if (!idStatuses.has(value.model_identity_status as string)) throw new Error("Unknown model identity");
  if (value.trace_status !== "verified_events" && value.trace_status !== "unavailable") throw new Error("Unknown trace status");
  if (!Array.isArray(value.trace_events)) throw new Error("Trace events must be array");
  if (value.trace_status === "unavailable" && value.trace_events.length) throw new Error("Cannot replay unverified events");
  if (value.trace_status === "verified_events" && !value.trace_events.length) throw new Error("Verified trace must have evidence");
  const seen = new Set<string>();
  for (const item of value.trace_events) {
    if (!isObject(item) || !string(item.event_id) || !string(item.stage) || !string(item.source_path) ||
       (item.observed_at !== undefined && !string(item.observed_at)) || seen.has(String(item.event_id)))
      throw new Error("Invalid/duplicate trace event");
    seen.add(String(item.event_id));
  }
  if (value.usage !== undefined) checkUsage(value.usage);
  if (value.provenance && p.evidence_kind === "synthetic_ui_demo" && p.verification === "independently_reproduced")
    throw new Error("Demo cannot become reproduced research");
  return value as ResearchCase;
}
export function parseResearchCases(raw: unknown): ResearchCase[] {
  if (!Array.isArray(raw)) throw new Error("Expected case array");
  const cases = raw.map(parseResearchCase);
  const ids = new Set<string>();
  for (const c of cases) {
    const key = [c.experiment_id,c.case_id,c.arm_id ?? "none"].join("/");
    if (ids.has(key)) throw new Error("Duplicate experiment/case/arm");
    ids.add(key);
  }
  return cases;
}
