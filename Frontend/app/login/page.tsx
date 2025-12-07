"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import BehumanLogo from "@/components/BehumanLogo";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { OnboardingService } from "@/lib/onboarding-service";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { error, data } = await signIn(email, password);

      if (error) {
        toast.error("Error al iniciar sesión", {
          description: error.message === "Invalid login credentials"
            ? "Correo electrónico o contraseña incorrectos"
            : error.message,
        });
      } else if (data?.user) {
        toast.success("Inicio de sesión exitoso");

        // Check if user has completed onboarding
        const hasCompleted = await OnboardingService.hasCompletedOnboarding(data.user.id);

        if (hasCompleted) {
          router.push("/app");
        } else {
          router.push("/onboarding");
        }
      }
    } catch {
      toast.error("Error al iniciar sesión", {
        description: "Ocurrió un error inesperado. Por favor, intenta de nuevo.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header with logo - Mobile optimized */}
      <div className="flex-shrink-0 pt-8 pb-4 px-6">
        <div className="text-center space-y-2">
          <BehumanLogo size={56} className="mx-auto" />
          <h1 className="text-xl font-bold text-foreground">behuman</h1>
        </div>
      </div>

      {/* Main content - Centered and mobile optimized */}
      <div className="flex-1 flex flex-col justify-center px-6 pb-8">
        <div className="w-full max-w-sm mx-auto space-y-6">
          <div className="space-y-1 text-center">
            <h2 className="text-2xl font-bold text-foreground">
              Bienvenido de vuelta
            </h2>
            <p className="text-sm text-muted-foreground">
              Ingresa tus credenciales para continuar
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-12 text-base"
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-sm">Contraseña</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-12 text-base pr-12"
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                  disabled={isLoading}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-medium mt-2"
              disabled={isLoading}
            >
              {isLoading ? "Iniciando sesión..." : "Iniciar sesión"}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            ¿No tienes cuenta?
          </p>

          <Link href="/register" className="block">
            <Button
              variant="outline"
              className="w-full h-12 text-base font-medium"
              disabled={isLoading}
            >
              Crear una cuenta
            </Button>
          </Link>
        </div>
      </div>

      {/* Footer - Fixed at bottom on mobile */}
      <div className="flex-shrink-0 pb-6 px-6">
        <p className="text-center text-xs text-muted-foreground leading-relaxed">
          Al continuar, aceptas nuestros{" "}
          <Link href="#" className="text-primary hover:underline">
            Términos de servicio
          </Link>{" "}
          y{" "}
          <Link href="#" className="text-primary hover:underline">
            Política de privacidad
          </Link>
        </p>
      </div>
    </div>
  );
}
