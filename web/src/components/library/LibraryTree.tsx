import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { LibraryNode } from "@/api";
import { DueBadge } from "@/components/DueBadge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Progress } from "@/components/ui/progress";
import { reviewUrl } from "@/lib/format";
import { cn } from "@/lib/utils";

interface LibraryTreeProps {
  nodes: LibraryNode[];
  showMastery?: boolean;
  filter?: string;
  defaultExpanded?: boolean;
}

function matchesFilter(node: LibraryNode, filter: string): boolean {
  const q = filter.toLowerCase();
  if (node.label.toLowerCase().includes(q)) return true;
  return node.children.some((child) => matchesFilter(child, q));
}

function filterNodes(nodes: LibraryNode[], filter: string): LibraryNode[] {
  if (!filter.trim()) return nodes;
  return nodes
    .filter((node) => matchesFilter(node, filter))
    .map((node) => ({
      ...node,
      children: filterNodes(node.children, filter),
    }));
}

function TreeNode({
  node,
  showMastery,
  defaultExpanded,
}: {
  node: LibraryNode;
  showMastery?: boolean;
  defaultExpanded?: boolean;
}) {
  const hasChildren = node.children.length > 0;
  const focusDeck = node.kind === "module" ? node.path ?? node.id : null;
  const focusConcept = node.kind === "topic" ? node.slug ?? node.id : null;
  const mastery = node.mastery_score ?? 0;

  if (!hasChildren) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border bg-card/40 px-3 py-2">
        <span className="text-sm font-medium">{node.label}</span>
        <div className="flex items-center gap-2">
          <DueBadge count={node.due_count} />
          {showMastery && node.mastery_score != null && (
            <span
              className={cn(
                "text-xs",
                mastery < 50 ? "text-red-300" : "text-green-300",
              )}
            >
              {mastery.toFixed(0)}%
            </span>
          )}
          {node.due_count > 0 && (
            <Button asChild variant="ghost" size="sm">
              <Link to={reviewUrl(focusDeck, focusConcept)}>Review</Link>
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <Collapsible defaultOpen={defaultExpanded}>
      <div className="rounded-lg border bg-card/40">
        <div className="flex items-center gap-2 px-3 py-2">
          <CollapsibleTrigger className="group flex flex-1 items-center gap-2 text-left">
            <ChevronRight className="h-4 w-4 shrink-0 transition-transform group-data-[state=open]:rotate-90" />
            <span className="text-sm font-medium">{node.label}</span>
          </CollapsibleTrigger>
          <div className="flex items-center gap-2">
            <DueBadge count={node.due_count} />
            <span className="hidden text-xs text-muted-foreground sm:inline">
              {node.card_count} cards
            </span>
            {showMastery && node.mastery_score != null && (
              <span className="hidden w-12 text-right text-xs sm:inline">
                {mastery.toFixed(0)}%
              </span>
            )}
            {node.due_count > 0 && (
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link to={reviewUrl(focusDeck, focusConcept)}>Review</Link>
              </Button>
            )}
          </div>
        </div>
        {showMastery && node.mastery_score != null && (
          <div className="px-3 pb-2">
            <Progress value={mastery} className="h-1.5" />
          </div>
        )}
        <CollapsibleContent className="space-y-1 border-t px-3 py-2">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} showMastery={showMastery} />
          ))}
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

export function LibraryTree({
  nodes,
  showMastery,
  filter = "",
  defaultExpanded,
}: LibraryTreeProps) {
  const filtered = filterNodes(nodes, filter);
  if (filtered.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No matches for your search.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {filtered.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          showMastery={showMastery}
          defaultExpanded={defaultExpanded}
        />
      ))}
    </div>
  );
}
