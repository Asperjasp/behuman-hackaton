import { User } from "lucide-react";
import { cn } from "@/lib/utils";

interface UserVideoPreviewProps {
  isCameraOn: boolean;
  className?: string;
}

const UserVideoPreview = ({ isCameraOn, className }: UserVideoPreviewProps) => {
  return (
    <div className={cn(
      "w-24 h-32 rounded-2xl overflow-hidden bg-muted border-2 border-background shadow-xl transition-all",
      className
    )}>
      {isCameraOn ? (
        <div className="w-full h-full bg-gradient-to-b from-muted to-muted-foreground/20 flex items-center justify-center">
          {/* Placeholder for actual video feed */}
          <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="w-6 h-6 text-primary" />
          </div>
        </div>
      ) : (
        <div className="w-full h-full bg-muted flex items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-muted-foreground/20 flex items-center justify-center">
            <User className="w-6 h-6 text-muted-foreground" />
          </div>
        </div>
      )}
    </div>
  );
};

export default UserVideoPreview;
