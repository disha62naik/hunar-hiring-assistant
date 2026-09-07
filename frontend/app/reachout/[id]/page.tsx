"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { ReachoutSearch, CandidateWithCall } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";

function statusVariant(status: string) {
  if (status === "COMPLETED") return "success" as const;
  if (["FAILED", "NOT_CONNECTED", "CANCELLED"].includes(status)) return "destructive" as const;
  if (["RINGING", "IN_PROGRESS", "INITIATED", "SCHEDULED"].includes(status)) return "warning" as const;
  return "secondary" as const;
}

function zipQA(questions: string[], answers: Record<string, string> | null | undefined) {
  if (!answers) return [];
  return questions.map((q, i) => ({ question: q, answer: answers[`answer_${i + 1}`] || "—" }));
}

export default function ReachoutDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [search, setSearch] = useState<ReachoutSearch | null>(null);
  const [candidates, setCandidates] = useState<CandidateWithCall[]>([]);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<CandidateWithCall | null>(null);

  async function load() {
    const data = await api.getReachoutSearch(id);
    setSearch(data.search);
    setCandidates(data.candidates);
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleTriggerCalls() {
    setBusy(true);
    try {
      await api.triggerReachoutCalls(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function handleRetryAgent() {
    setBusy(true);
    try {
      await api.retryCreateReachoutAgent(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (!search) return <p className="text-sm text-muted-foreground">Loading...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Reachout search #{search.id}</h1>
        <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">{search.job_description}</p>
        <div className="flex flex-wrap gap-2 mt-3 text-xs text-muted-foreground">
          {search.criteria?.titles?.map((t, i) => <Badge key={i} variant="outline">{t}</Badge>)}
          {search.criteria?.location && <Badge variant="outline">{search.criteria.location}</Badge>}
        </div>
      </div>

      {!search.hunar_agent_id && (
        <div className="flex items-center justify-between rounded-md border border-destructive/50 bg-destructive/5 p-3 text-sm">
          <span>The Hunar voice agent for this search didn&apos;t get created yet.</span>
          <Button variant="outline" size="sm" onClick={handleRetryAgent} disabled={busy}>
            Retry agent creation
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Matched candidates ({candidates.length})</h2>
        <Button onClick={handleTriggerCalls} disabled={busy || candidates.length === 0 || !search.hunar_agent_id}>
          {busy ? "Working..." : "Reach out to all"}
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Company</TableHead>
            <TableHead>Call status</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {candidates.map((cw) => (
            <TableRow key={cw.candidate.id}>
              <TableCell>{cw.candidate.name}</TableCell>
              <TableCell>{cw.candidate.title || "—"}</TableCell>
              <TableCell>{cw.candidate.company || "—"}</TableCell>
              <TableCell>
                <Badge variant={statusVariant(cw.call?.status || "pending")}>
                  {cw.call?.status || "pending"}
                </Badge>
              </TableCell>
              <TableCell>
                {cw.call?.status === "COMPLETED" && (
                  <Button variant="outline" size="sm" onClick={() => setSelected(cw)}>View</Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selected && (
        <Card>
          <CardHeader><CardTitle>{selected.candidate.name} — call details</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {selected.call?.duration_seconds != null && (
              <p className="text-sm text-muted-foreground">
                Call duration: {Math.round(selected.call.duration_seconds)}s
              </p>
            )}
            {selected.call?.recording_url && (
              <div className="space-y-1">
                <p className="text-sm font-medium">Recording</p>
                <audio controls src={selected.call.recording_url} className="w-full" />
              </div>
            )}
            {selected.call?.answers && (
              <ul className="list-disc pl-5 text-sm space-y-1">
                {zipQA(search.reachout_questions, selected.call.answers).map(({ question, answer }) => (
                  <li key={question}><span className="font-medium">{question}:</span> {answer}</li>
                ))}
              </ul>
            )}
            <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>Close</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
