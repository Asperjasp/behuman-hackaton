"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import BehumanLogo from "@/components/BehumanLogo";
import { Eye, EyeOff, Check } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { toast } from "sonner";

export default function RegisterPage() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { error } = await signUp(email, password, {
        name,
        age: parseInt(age),
      });

      if (error) {
        toast.error("Error al crear la cuenta", {
          description: error.message === "User already registered"
            ? "Este correo electrónico ya está registrado"
            : error.message,
        });
      } else {
        toast.success("Cuenta creada exitosamente");
        router.push("/onboarding");
      }
    } catch {
      toast.error("Error al crear la cuenta", {
        description: "Ocurrió un error inesperado. Por favor, intenta de nuevo.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordRequirements = [
    { label: "Al menos 8 caracteres", met: password.length >= 8 },
    { label: "Una letra mayúscula", met: /[A-Z]/.test(password) },
    { label: "Un número", met: /\d/.test(password) },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header with logo - Mobile optimized */}
      <div className="flex-shrink-0 pt-8 pb-4 px-6">
        <div className="text-center space-y-2">
          <BehumanLogo size={56} className="mx-auto" />
          <h1 className="text-xl font-bold text-foreground">behuman</h1>
        </div>
      </div>

      {/* Main content - Scrollable on mobile */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="w-full max-w-sm mx-auto space-y-5">
          <div className="space-y-1 text-center">
            <h2 className="text-2xl font-bold text-foreground">
              Crea tu cuenta
            </h2>
            <p className="text-sm text-muted-foreground">
              Comienza tu viaje hacia una vida más saludable
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-sm">Nombre completo</Label>
              <Input
                id="name"
                type="text"
                placeholder="Tu nombre"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-12 text-base"
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="age" className="text-sm">Edad</Label>
              <Input
                id="age"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                placeholder="Tu edad"
                value={age}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '');
                  if (value === '' || (parseInt(value) >= 1 && parseInt(value) <= 120)) {
                    setAge(value);
                  }
                }}
                className="h-12 text-base"
                maxLength={3}
                required
                disabled={isLoading}
              />
            </div>

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
              {password && (
                <div className="space-y-1.5 pt-2">
                  {passwordRequirements.map((req, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-2 text-xs transition-colors ${
                        req.met ? "text-primary" : "text-muted-foreground"
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${
                          req.met ? "bg-primary" : "bg-muted"
                        }`}
                      >
                        {req.met && <Check className="w-2.5 h-2.5 text-primary-foreground" />}
                      </div>
                      {req.label}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-start space-x-3 pt-1">
              <Checkbox
                id="terms"
                checked={acceptTerms}
                onCheckedChange={(checked) => setAcceptTerms(checked as boolean)}
                className="mt-0.5"
                disabled={isLoading}
              />
              <Label htmlFor="terms" className="text-xs font-normal leading-relaxed cursor-pointer">
                Acepto los{" "}
                <Link href="#" className="text-primary hover:underline">
                  Términos de servicio
                </Link>{" "}
                y la{" "}
                <Link href="#" className="text-primary hover:underline">
                  Política de privacidad
                </Link>
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-medium"
              disabled={!acceptTerms || isLoading}
            >
              {isLoading ? "Creando cuenta..." : "Crear cuenta"}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            ¿Ya tienes cuenta?
          </p>

          <Link href="/login" className="block">
            <Button
              variant="outline"
              className="w-full h-12 text-base font-medium"
              disabled={isLoading}
            >
              Iniciar sesión
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
