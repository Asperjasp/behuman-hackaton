import { cn } from "@/lib/utils";

interface OnboardingOptionProps {
  label: string;
  selected: boolean;
  onClick: () => void;
  multiSelect?: boolean;
}

const OnboardingOption = ({ label, selected, onClick, multiSelect = false }: OnboardingOptionProps) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full px-4 py-3.5 rounded-xl text-left transition-all duration-200",
        "border-2 text-sm font-medium",
        selected
          ? "border-primary bg-primary/10 text-foreground"
          : "border-border bg-card text-foreground hover:border-primary/50 hover:bg-muted/50"
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex-shrink-0 w-5 h-5 border-2 transition-all duration-200 flex items-center justify-center",
            multiSelect ? "rounded-md" : "rounded-full",
            selected ? "border-primary bg-primary" : "border-muted-foreground/40"
          )}
        >
          {selected && (
            <svg
              className="w-3 h-3 text-primary-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={3}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
        <span>{label}</span>
      </div>
    </button>
  );
};

export default OnboardingOption;
