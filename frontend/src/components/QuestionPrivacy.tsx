import type { QuestionStatus } from "@/api/client";

interface QuestionPrivacyProps {
  /** The answer generator the API reports; unknown until status loads. */
  generator: QuestionStatus["generator"] | undefined;
  /** Whether limited prior conversation is sent too (the filing reader's side chat). */
  withConversation?: boolean;
  id?: string;
  className?: string;
}

/** Where a question goes, stated for the generator actually in use (ADR 0022 / ADR 0029). */
export function QuestionPrivacy({
  generator,
  withConversation = false,
  id,
  className,
}: QuestionPrivacyProps) {
  const sent = withConversation
    ? "Your question, limited prior conversation and public filing excerpts"
    : "Your question and relevant public filing excerpts";
  return (
    <p id={id} className={className}>
      {generator === "ollama"
        ? `${sent} are processed on a model server run by this Orbit deployment's owner. They are not sent to an outside AI service. Keep personal or confidential information out of your question.`
        : `${sent} are sent to Google’s Gemini service. Google may use free-tier submissions to improve its products. Keep personal or confidential information out of your question.`}
    </p>
  );
}
