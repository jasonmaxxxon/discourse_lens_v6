// Shared markdown renderer helper
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PropsWithChildren } from "react";

export const MarkdownContent = ({ children }: PropsWithChildren) => {
  const text = typeof children === "string" ? children : "";
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-invert max-w-none prose-sm">
      {text}
    </ReactMarkdown>
  );
};

export default MarkdownContent;
