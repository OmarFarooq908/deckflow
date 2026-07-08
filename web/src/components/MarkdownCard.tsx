import ReactMarkdown from "react-markdown";

interface MarkdownCardProps {
  content: string;
}

export function MarkdownCard({ content }: MarkdownCardProps) {
  return (
    <div className="markdown">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
