import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-foreground">404</h1>
        <h2 className="text-2xl font-semibold text-foreground">Página no encontrada</h2>
        <p className="text-muted-foreground max-w-md">
          Lo sentimos, la página que estás buscando no existe o ha sido movida.
        </p>
        <Link href="/">
          <Button className="mt-4">
            Volver al inicio
          </Button>
        </Link>
      </div>
    </div>
  );
}
