import { Loader2 } from "lucide-react";
import { Progress } from "./ui/progress";
import { useState, useEffect } from "react";

export function LoadingState() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + 10;
      });
    }, 300);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-16 px-8">
      <div className="w-full max-w-md space-y-6">
        <div className="flex justify-center">
          <div className="p-6 rounded-full bg-primary/10">
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
          </div>
        </div>
        
        <div className="space-y-3">
          <Progress value={progress} className="h-2" />
          <p className="text-center text-muted-foreground">
            Analizando con IA... Este proceso puede tardar unos segundos.
          </p>
        </div>
      </div>
    </div>
  );
}
