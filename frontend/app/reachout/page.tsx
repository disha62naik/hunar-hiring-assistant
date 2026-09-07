"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ReachoutPage() {
  const router = useRouter();
  const [jd, setJd] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.createReachoutSearch({
        job_description: jd,
        location: location || undefined,
        max_results: 20,
      });
      router.push(`/reachout/${result.search.id}`);
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
          <CardTitle>Find and reach out to candidates</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="jd">Job description</Label>
              <Textarea id="jd" value={jd} onChange={(e) => setJd(e.target.value)} required rows={8} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="location">Location (optional override)</Label>
              <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Bengaluru, India" />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Search candidates"}
            </Button>
            <p className="text-xs text-muted-foreground">
              This calls your configured people-search provider (Apollo.io or PDL) and can take
              a few seconds, especially if phone-number reveal calls are involved.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
