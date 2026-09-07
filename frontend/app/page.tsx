import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <Link href="/screenings">
        <Card className="h-full hover:border-primary transition-colors">
          <CardHeader>
            <CardTitle>Project 1 — AI Hiring Assistant</CardTitle>
            <CardDescription>
              Create a screening from a job description, add candidates, and let a
              Hunar voice agent conduct the phone screen.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Go to Screenings →</CardContent>
        </Card>
      </Link>
      <Link href="/reachout">
        <Card className="h-full hover:border-primary transition-colors">
          <CardHeader>
            <CardTitle>Project 2 — People Search &amp; Reachout</CardTitle>
            <CardDescription>
              Paste a job description, find matching candidates, and reach out to
              them by voice call.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Go to Reachout →</CardContent>
        </Card>
      </Link>
    </div>
  );
}
