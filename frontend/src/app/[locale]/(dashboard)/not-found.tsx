import { Link } from "@/i18n/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

export default function DashboardNotFound() {
  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="text-5xl font-bold tracking-tight">
            404
          </CardTitle>
          <CardDescription>
            This page doesn&apos;t exist. It may have been moved or removed.
          </CardDescription>
        </CardHeader>
        <CardContent />
        <CardFooter className="justify-center">
          <Button asChild>
            <Link href="/">Go to dashboard</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
