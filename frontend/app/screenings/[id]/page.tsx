"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Screening, CandidateWithCall } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";

function statusVariant(status: string) {
  if (status === "COMPLETED") return "success" as const;
  if (["FAILED", "NOT_CONNECTED", "CANCELLED"].includes(status)) return "destructive" as const;
  if (["RINGING", "IN_PROGRESS", "INITIATED", "SCHEDULED"].includes(status)) return "warning" as const;
  return "secondary" as const; // pending / NOT_STARTED
}

function zipQA(questions: string[], answers: Record<string, string> | null | undefined) {
  if (!answers) return [];
  return questions.map((q, i) => ({ question: q, answer: answers[`answer_${i + 1}`] || "—" }));
}

export default function ScreeningDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [screening, setScreening] = useState<Screening | null>(null);
  const [candidates, setCandidates] = useState<CandidateWithCall[]>([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<CandidateWithCall | null>(null);

  async function load() {
    const data = await api.getScreening(id);
    setScreening(data.screening);
    setCandidates(data.candidates);
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000); // poll for call status updates
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleAddCandidate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.addCandidates(id, [{ name, phone }]);
      setName("");
      setPhone("");
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function handleTriggerCalls() {
    setBusy(true);
    try {
      await api.triggerScreeningCalls(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function handleRetryAgent() {
    setBusy(true);
    try {
      await api.retryCreateScreeningAgent(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (!screening) return <p className="text-sm text-muted-foreground">Loading...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">{screening.title}</h1>
        <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">{screening.job_description}</p>
        <div className="flex flex-wrap gap-2 mt-3">
          {screening.questions.map((q, i) => (
            <Badge key={i} variant="outline">{q}</Badge>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Add candidate</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleAddCandidate} className="flex flex-wrap gap-3 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="phone">Phone (E.164, e.g. +919876543210)</Label>
              <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} required />
            </div>
            <Button type="submit" disabled={busy}>Add</Button>
          </form>
        </CardContent>
      </Card>

      {!screening.hunar_agent_id && (
        <div className="flex items-center justify-between rounded-md border border-destructive/50 bg-destructive/5 p-3 text-sm">
          <span>The Hunar voice agent for this screening didn&apos;t get created yet.</span>
          <Button variant="outline" size="sm" onClick={handleRetryAgent} disabled={busy}>
            Retry agent creation
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Candidates ({candidates.length})</h2>
        <Button onClick={handleTriggerCalls} disabled={busy || candidates.length === 0 || !screening.hunar_agent_id}>
          {busy ? "Working..." : "Trigger calls for all candidates"}
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Call status</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {candidates.map((cw) => (
            <TableRow key={cw.candidate.id}>
              <TableCell>{cw.candidate.name}</TableCell>
              <TableCell>{cw.candidate.phone}</TableCell>
              <TableCell>
                <Badge variant={statusVariant(cw.call?.status || "pending")}>
                  {cw.call?.status || "pending"}
                </Badge>
              </TableCell>
              <TableCell>
                {cw.call?.status === "COMPLETED" && (
                  <Button variant="outline" size="sm" onClick={() => setSelected(cw)}>
                    View results
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selected && (
        <Card>
          <CardHeader>
            <CardTitle>{selected.candidate.name} — call details</CardTitle>
          </CardHeader>
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
              <div className="space-y-1">
                <p className="text-sm font-medium">Answers</p>
                <ul className="list-disc pl-5 text-sm space-y-1">
                  {zipQA(screening.questions, selected.call.answers).map(({ question, answer }) => (
                    <li key={question}><span className="font-medium">{question}:</span> {answer}</li>
                  ))}
                </ul>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>Close</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
