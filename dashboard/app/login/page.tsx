import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-cornerstone-navy px-4">
      <div className="flex w-full max-w-sm flex-col items-center rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="mb-6 text-xl font-bold text-cornerstone-navy">
          Cornerstone - Dashboard de Harmony
        </h1>
        <LoginForm />
      </div>
    </main>
  );
}
