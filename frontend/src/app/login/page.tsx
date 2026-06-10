"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/feedback";
import { useSession } from "@/store/session";

export default function LoginPage() {
  const router = useRouter();
  const login = useSession((s) => s.login);
  const loading = useSession((s) => s.loading);
  const error = useSession((s) => s.error);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await login(email, password);
    if (ok) router.replace("/overview");
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardBody className="space-y-5">
          <div>
            <h1 className="text-lg font-semibold text-slate-100">Sign in</h1>
            <p className="text-sm text-slate-500">Welcome back to your analytics.</p>
          </div>
          <form onSubmit={onSubmit} className="space-y-4">
            <Input
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              id="password"
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {error ? <p className="text-xs text-status-danger">{error}</p> : null}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? <Spinner className="h-4 w-4" /> : null}
              Sign in
            </Button>
          </form>
          <p className="text-center text-xs text-slate-500">
            No account?{" "}
            <Link href="/register" className="text-brand hover:underline">
              Create one
            </Link>
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
