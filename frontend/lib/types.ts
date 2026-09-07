export interface Screening {
  id: number;
  title: string;
  job_description: string;
  questions: string[];
  hunar_agent_id?: string | null;
  created_at: string;
}


export type CallStatus =
  | "pending"
  | "NOT_STARTED"
  | "SCHEDULED"
  | "INITIATED"
  | "RINGING"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "NOT_CONNECTED"
  | "CANCELLED"
  | "FAILED";

export interface Call {
  id: number;
  candidate_id: number;
  hunar_call_id?: string | null;
  request_id?: string | null;
  status: CallStatus;
  // Hunar exposes no raw transcript -- only a recording URL and a
  // structured result. `answers` keys are answer_1, answer_2... in the
  // same order as the screening/search's question list (zip by index).
  recording_url?: string | null;
  answers?: Record<string, string> | null;
  duration_seconds?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Candidate {
  id: number;
  screening_id?: number | null;
  reachout_search_id?: number | null;
  name: string;
  phone: string;
  email?: string | null;
  title?: string | null;
  company?: string | null;
  source: "manual" | "people_search";
  created_at: string;
}

export interface CandidateWithCall {
  candidate: Candidate;
  call: Call | null;
}

export interface ReachoutSearch {
  id: number;
  job_description: string;
  criteria: { titles?: string[]; skills?: string[]; location?: string | null };
  reachout_questions: string[];
  hunar_agent_id?: string | null;
  created_at: string;
}
