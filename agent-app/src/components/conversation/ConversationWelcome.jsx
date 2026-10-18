/** The same editorial welcome layout for the general agent and philosophers. */
export default function ConversationWelcome({ name, greeting, children }) {
  return <div className="cw-empty cw-empty-general">
    <h1 className="cw-brand-wordmark" aria-label="PhiAgent">PHIAGENT</h1>
    <div className="cw-brand-caption"><span>{name}</span><span aria-hidden="true">·</span><span>{greeting}</span></div>
    {children}
  </div>;
}
