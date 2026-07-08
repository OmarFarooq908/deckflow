import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { parseDeckPath } from "@/lib/format";

interface DeckBreadcrumbProps {
  deckPath: string;
  className?: string;
}

export function DeckBreadcrumb({ deckPath, className }: DeckBreadcrumbProps) {
  const segments = parseDeckPath(deckPath);
  if (segments.length === 0) return null;

  return (
    <Breadcrumb className={className}>
      <BreadcrumbList>
        {segments.map((segment, index) => {
          const isLast = index === segments.length - 1;
          return (
            <BreadcrumbItem key={`${segment}-${index}`}>
              {isLast ? (
                <BreadcrumbPage>{segment}</BreadcrumbPage>
              ) : (
                <span className="text-muted-foreground">{segment}</span>
              )}
              {!isLast && <BreadcrumbSeparator />}
            </BreadcrumbItem>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
