"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/feedback";
import { useSession } from "@/store/session";

export default function RegisterPage() {
  const router = useRouter();
  const register = useSession((s) => s.register);
  const loading = useSession((s) => s.loading);
  const error = useSession((s) => s.error);

  const [form, setForm] = useState({
    full_name: "",
    organization_name: "",
    email: "",
    password: "",
  });

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await register(form);
    if (ok) router.replace("/overview");
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardBody className="space-y-5">
          <div>
            <h1 className="text-lg font-semibold text-slate-100">Create your workspace</h1>
            <p className="text-sm text-slate-500">Start tracking events in minutes.</p>
          </div>
          <form onSubmit={onSubmit} className="space-y-4">
            <Input id="full_name" label="Full name" required value={form.full_name} onChange={update("full_name")} />
            <Input
              id="organization_name"
              label="Organization"
              required
              value={form.organization_name}
              onChange={update("organization_name")}
            />
            <Input id="email" label="Email" type="email" autoComplete="email" required value={form.email} onChange={update("email")} />
            <Input
              id="password"
              label="Password (min 8 chars)"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={form.password}
              onChange={update("password")}
            />
            {error ? <p className="text-xs text-status-danger">{error}</p> : null}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? <Spinner className="h-4 w-4" /> : null}
              Create account
            </Button>
          </form>
          <p className="text-center text-xs text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="text-brand hover:underline">
              Sign in
            </Link>
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
