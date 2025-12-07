import { cn } from "@/lib/utils";

interface TranscriptionOverlayProps {
  text: string;
  isVisible: boolean;
  className?: string;
}

const TranscriptionOverlay = ({ text, isVisible, className }: TranscriptionOverlayProps) => {
  if (!isVisible || !text) return null;

  return (
    <div className={cn(
      "absolute bottom-4 left-4 right-4 transition-all duration-300",
      isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
      className
    )}>
      <div className="bg-background/80 backdrop-blur-md rounded-2xl px-4 py-3 shadow-lg">
        <p className="text-foreground text-center text-sm leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
};

export default TranscriptionOverlay;
