"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Spinner } from "@/components/ui/feedback";
import { useSession } from "@/store/session";

/** Landing route: send authenticated users to the dashboard, others to login. */
export default function Home() {
  const router = useRouter();
  const token = useSession((s) => s.token);

  useEffect(() => {
    router.replace(token ? "/overview" : "/login");
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}
