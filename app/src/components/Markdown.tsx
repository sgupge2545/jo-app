import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

type Props = {
  content: string;
};

export const Markdown = ({ content }: Props) => {
  return (
    <div className="markdown-body prose dark:prose-invert text-gray-800 dark:text-gray-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={{
          a: ({ ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 truncate inline-block max-w-[800px] align-middle"
            >
              {props.children}
            </a>
          ),
          table({ children }) {
            return (
              <table className="border-collapse border border-black px-3 py-1 dark:border-white">
                {children}
              </table>
            );
          },
          th({ children }) {
            return (
              <th className="break-words border border-black bg-gray-500 px-3 py-1 text-white dark:border-white">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="break-words border border-black px-3 py-1 dark:border-white">
                {children}
              </td>
            );
          },
          li({ children }) {
            return <li className="mb-1">{children}</li>;
          },
          h2({ children }) {
            return (
              <h2 className="text-gray-800 dark:text-gray-100">{children}</h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-gray-800 dark:text-gray-100">{children}</h3>
            );
          },
          br: () => <br />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
