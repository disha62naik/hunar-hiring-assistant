"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Screening } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ScreeningsPage() {
  const [screenings, setScreenings] = useState<Screening[]>([]);
  const [title, setTitle] = useState("");
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setScreenings(await api.listScreenings());
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.createScreening({ title, job_description: jd });
      setTitle("");
      setJd("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>New screening</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="title">Role title</Label>
              <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="jd">Job description</Label>
              <Textarea id="jd" value={jd} onChange={(e) => setJd(e.target.value)} required rows={6} />
              <p className="text-xs text-muted-foreground">
                Screening questions are auto-generated from this JD (or set ANTHROPIC_API_KEY
                for LLM-generated questions — otherwise a sensible default set is used).
              </p>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create screening"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Screenings</h2>
        {screenings.length === 0 && <p className="text-sm text-muted-foreground">None yet.</p>}
        {screenings.map((s) => (
          <Link key={s.id} href={`/screenings/${s.id}`}>
            <Card className="hover:border-primary transition-colors">
              <CardHeader>
                <CardTitle className="text-base">{s.title}</CardTitle>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
