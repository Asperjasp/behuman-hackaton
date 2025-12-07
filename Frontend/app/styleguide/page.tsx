"use client";

import BehumanLogo from "@/components/BehumanLogo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export default function Styleguide() {
  return (
    <main className="min-h-screen bg-background p-8 md:p-12">
      <div className="mx-auto max-w-4xl space-y-12">
        {/* Header */}
        <header className="space-y-4">
          <div className="flex items-center gap-4">
            <BehumanLogo size={64} />
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground">behuman</h1>
              <p className="text-muted-foreground">Style Guide & Design System</p>
            </div>
          </div>
        </header>

        <Separator />

        {/* Logo Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Logo</h2>
          <div className="flex flex-wrap items-end gap-8">
            <div className="flex flex-col items-center gap-2">
              <BehumanLogo size={96} />
              <span className="text-sm text-muted-foreground">96px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <BehumanLogo size={64} />
              <span className="text-sm text-muted-foreground">64px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <BehumanLogo size={48} />
              <span className="text-sm text-muted-foreground">48px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <BehumanLogo size={32} />
              <span className="text-sm text-muted-foreground">32px</span>
            </div>
          </div>
        </section>

        <Separator />

        {/* Colors Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Colors</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            <ColorSwatch name="Primary" className="bg-primary" hsl="20 90% 55%" />
            <ColorSwatch name="Background" className="bg-background border" hsl="30 45% 95%" />
            <ColorSwatch name="Foreground" className="bg-foreground" hsl="0 0% 20%" />
            <ColorSwatch name="Secondary" className="bg-secondary" hsl="30 30% 90%" />
            <ColorSwatch name="Muted" className="bg-muted" hsl="30 20% 88%" />
            <ColorSwatch name="Accent" className="bg-accent" hsl="20 85% 60%" />
            <ColorSwatch name="Card" className="bg-card border" hsl="30 40% 98%" />
            <ColorSwatch name="Destructive" className="bg-destructive" hsl="0 84% 60%" />
          </div>
        </section>

        <Separator />

        {/* Typography Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Typography</h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Heading 1</p>
              <h1 className="text-4xl font-bold text-foreground">The quick brown fox</h1>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Heading 2</p>
              <h2 className="text-3xl font-semibold text-foreground">The quick brown fox</h2>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Heading 3</p>
              <h3 className="text-2xl font-semibold text-foreground">The quick brown fox</h3>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Body</p>
              <p className="text-base text-foreground">
                The quick brown fox jumps over the lazy dog. This is body text that demonstrates the default text styling.
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Muted</p>
              <p className="text-muted-foreground">
                This is muted text for secondary information.
              </p>
            </div>
          </div>
        </section>

        <Separator />

        {/* Buttons Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Buttons</h2>
          <div className="flex flex-wrap gap-4">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>
          </div>
          <div className="flex flex-wrap gap-4">
            <Button size="sm">Small</Button>
            <Button size="default">Default</Button>
            <Button size="lg">Large</Button>
          </div>
        </section>

        <Separator />

        {/* Badges Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Badges</h2>
          <div className="flex flex-wrap gap-3">
            <Badge>Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Destructive</Badge>
          </div>
        </section>

        <Separator />

        {/* Inputs Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Inputs</h2>
          <div className="max-w-md space-y-4">
            <Input placeholder="Default input" />
            <Input placeholder="Disabled input" disabled />
          </div>
        </section>

        <Separator />

        {/* Cards Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">Cards</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Card Title</CardTitle>
                <CardDescription>Card description goes here</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  This is the card content area where you can add any content.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BehumanLogo size={24} />
                  With Logo
                </CardTitle>
                <CardDescription>A card with the behuman logo</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">Action Button</Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Footer */}
        <footer className="pt-8 text-center">
          <p className="text-sm text-muted-foreground">
            behuman © 2024 — Design System v1.0
          </p>
        </footer>
      </div>
    </main>
  );
};

const ColorSwatch = ({ name, className, hsl }: { name: string; className: string; hsl: string }) => (
  <div className="space-y-2">
    <div className={`h-20 rounded-lg ${className}`} />
    <div>
      <p className="font-medium text-foreground text-sm">{name}</p>
      <p className="text-xs text-muted-foreground">{hsl}</p>
    </div>
  </div>
);
