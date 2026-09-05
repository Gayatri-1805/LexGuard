/**
 * Auto-generated TypeScript types from OpenAPI schema.
 * 
 * This file is auto-generated from the FastAPI OpenAPI schema.
 * DO NOT EDIT MANUALLY — regenerate using: ./openapi-sync.sh
 * 
 * Generated: 2026-09-05
 * Source: api-and-sdk/api/main.py
 */

/**
 * Enum for claim types extracted from legal text.
 */
export enum ClaimType {
  CASE_CITATION = 'CASE_CITATION',
  SECTION_REF = 'SECTION_REF',
  HOLDING = 'HOLDING',
  PROCEDURAL = 'PROCEDURAL',
  OTHER = 'OTHER',
}

/**
 * An atomic legal claim extracted from LLM output.
 */
export interface Claim {
  /** Unique identifier for this claim within a CheckResponse */
  id: string;
  /** The atomic legal claim text as decomposed from the original LLM output */
  text: string;
  /** Classification of the claim type */
  type: ClaimType;
  /** Character offsets (start, end) in the original LLM output */
  span: [number, number];
}

/**
 * Enum for verdict labels from the hallucination detection pipeline.
 */
export enum VerdictLabel {
  ENTAILED = 'ENTAILED',
  CONTRADICTED = 'CONTRADICTED',
  NOT_ENOUGH_INFO = 'NOT_ENOUGH_INFO',
  LOW_RISK_SKIP = 'LOW_RISK_SKIP',
}

/**
 * The hallucination detection result for a single claim.
 */
export interface Verdict {
  /** Foreign key reference to Claim.id */
  claim_id: string;
  /** The hallucination classification */
  label: VerdictLabel;
  /** Retrieved passages or knowledge base text that support this verdict */
  evidence: string[];
  /** Pipeline stage that produced this verdict (1-4) */
  stage_reached: number;
  /** Confidence score (0-1) of the verdict */
  confidence?: number;
}

/**
 * Enum for final decision from the pipeline.
 */
export enum Decision {
  SAFE = 'SAFE',
  FLAGGED = 'FLAGGED',
  ABSTAIN = 'ABSTAIN',
}

/**
 * Input to the hallucination detection pipeline.
 */
export interface CheckRequest {
  /** The LLM-generated output text to check for hallucinations */
  text: string;
  /** Optional context or system prompt that produced the text */
  context?: string;
  /** Optional caller-supplied unique identifier for tracing */
  request_id?: string;
}

/**
 * Output from the hallucination detection pipeline.
 */
export interface CheckResponse {
  /** Unique identifier for this analysis request */
  request_id: string;
  /** List of atomic claims extracted from the input text */
  claims: Claim[];
  /** List of verdicts, one per claim */
  verdicts: Verdict[];
  /** Aggregate hallucination risk score (0-1) from Stage 4 */
  trust_index: number;
  /** Final decision: SAFE, FLAGGED, or ABSTAIN */
  decision: Decision;
  /** Timestamp when the analysis was completed (ISO 8601 UTC) */
  created_at: string;
}

/**
 * Aggregate analytics summary.
 */
export interface AnalyticsSummary {
  /** Total number of checks performed in the time window */
  total_checks: number;
  /** Average trust index across all checks */
  avg_trust_index: number;
  /** Count of checks with SAFE decision */
  safe_count: number;
  /** Count of checks with FLAGGED decision */
  flagged_count: number;
  /** Count of checks with ABSTAIN decision */
  abstain_count: number;
}
