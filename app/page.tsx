"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function Page() {
  // Renamed from ResumeTailor to Page
  const [role, setRole] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      // Create form data matching backend expectations
      const formData = new FormData();
      formData.append("role", role);
      formData.append("job_description_text", jobDescription);

      // Adjust the URL based on your backend's deployment
      // Using the rewritten API path
      const response = await fetch("/api/py/tailor_resume/", {
        // Updated endpoint
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to tailor resume");
      }

      const data = await response.json();

      if (data.download_link) {
        // Prepend '/api/py' to the download link to align with rewrites
        const downloadLink = data.download_link.startsWith("/")
          ? `/api/py${data.download_link}`
          : data.download_link;
        setResult(downloadLink);
      } else if (data.error) {
        setError(data.error);
      } else {
        setError("Unexpected response from server.");
      }
    } catch (error: any) {
      // TypeScript error handling
      console.error("Error:", error);
      setError(
        error.message ||
          "An error occurred while tailoring the resume. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="w-full max-w-3xl mx-auto">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Resume Tailor</CardTitle>
          <CardDescription>
            Enter the job details to generate a tailored resume
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                required
                placeholder="e.g. Software Engineer"
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="jobDescription">Job Description</Label>
              <Textarea
                id="jobDescription"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                required
                placeholder="Paste the job description here..."
                className="w-full min-h-[150px]"
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Tailoring Resume..." : "Tailor Resume"}
            </Button>
          </form>

          {result && (
            <Alert className="mt-6" variant="default">
              <CheckCircle2 className="h-4 w-4" />
              <AlertTitle>Success</AlertTitle>
              <AlertDescription>
                Your tailored resume is ready.
                <a
                  href={result}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary font-medium hover:underline ml-1"
                >
                  Download here
                </a>
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert className="mt-6" variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
