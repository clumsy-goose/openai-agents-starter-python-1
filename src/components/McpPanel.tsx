import { useCallback, useMemo, useState } from 'react';
import { useT, MessageKeys } from '../i18n';
import styles from './McpPanel.module.css';

/**
 * MCP surface of this deployment.
 *
 * `edgeone.json` sets `agents.mcp = { enabled: true, auth: "passthrough" }`,
 * which makes the EdgeOne Makers runtime expose every `agents/*` route as an
 * MCP tool on a single `/mcp` endpoint. So this list is derived from the agent
 * routes rather than hand-maintained:
 *
 *   agents/chat               → chat
 *   agents/stop               → cancel_run
 *   agents/get_weather        → get_weather
 *   agents/get_clothing_advice → get_clothing_advice
 *   agents/translate_text     → translate_text
 *   agents/text_statistics    → text_statistics
 *
 * The four tool routes were split out of `_tools.ts` specifically to verify
 * that auto-registration works: none of them contain MCP-specific code.
 */
const MCP_SERVER_NAME = 'makers-agent';

/**
 * Resolve the MCP endpoint from the current browser location so the displayed
 * config/verify snippets always point at the domain the user is actually
 * viewing (dev: localhost, prod: the deployed domain). Falls back to a relative
 * `/mcp` when `window` is unavailable (e.g. non-browser build environments).
 */
function getMcpEndpoint(): string {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}/mcp`;
  }
  return '/mcp';
}

function buildMcpConfig(endpoint: string): string {
  return `{
  "mcpServers": {
    "${MCP_SERVER_NAME}": {
      "url": "${endpoint}",
      "headers": {
        "Authorization": "Bearer <your-user-token>"
      }
    }
  }
}`;
}

interface McpTool {
  name: string;
  route: string;
  /** Tools split out of the agent purely to prove MCP auto-registration. */
  autoRegistered: boolean;
  descKey: MessageKeys;
}

const MCP_TOOLS: McpTool[] = [
  { name: 'chat',               route: 'agents/chat',               autoRegistered: false, descKey: 'mcp.tool.chat' },
  { name: 'cancel_run',         route: 'agents/stop',               autoRegistered: false, descKey: 'mcp.tool.cancelRun' },
  { name: 'get_weather',        route: 'agents/get_weather',        autoRegistered: true,  descKey: 'mcp.agentTool.weather' },
  { name: 'get_clothing_advice', route: 'agents/get_clothing_advice', autoRegistered: true, descKey: 'mcp.agentTool.clothing' },
  { name: 'translate_text',     route: 'agents/translate_text',     autoRegistered: true,  descKey: 'mcp.agentTool.translate' },
  { name: 'text_statistics',    route: 'agents/text_statistics',    autoRegistered: true,  descKey: 'mcp.agentTool.statistics' },
];

/** Sample calls for checking auto-registration against a live deployment. */
function buildVerifySnippet(endpoint: string): string {
  return `# All requests need a makers-conversation-id header (6-36 chars, [0-9a-zA-Z-_.])
CID="makers-conversation-id: verify-001"

# 1. List tools — all 6 routes appear with no MCP-specific code
curl -sX POST "${endpoint}" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" -H "$CID" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# 2. Call over MCP. The runtime advertises the same fixed schema
#    { message, session_id } for every route, so pass JSON inside message.
curl -sX POST "${endpoint}" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" -H "$CID" \\
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather",
       "arguments":{"message":"{\\"city\\":\\"Beijing\\"}"}}}'

# 3. Or call the route directly with its real structured arguments
curl -sX POST "$(echo "${endpoint}" | sed 's#/mcp$##')/get_weather" \\
  -H "Content-Type: application/json" -H "$CID" \\
  -d '{"city":"Beijing"}'`;
}

export default function McpPanel() {
  const { t } = useT();
  const [expanded, setExpanded] = useState(true);
  const [copied, setCopied] = useState<'config' | 'verify' | null>(null);

  // Derive the MCP endpoint (and the snippets that embed it) from the current
  // browser URL, so the panel always reflects the domain being viewed.
  const mcpEndpoint = useMemo(() => getMcpEndpoint(), []);
  const mcpConfig = useMemo(() => buildMcpConfig(mcpEndpoint), [mcpEndpoint]);
  const verifySnippet = useMemo(() => buildVerifySnippet(mcpEndpoint), [mcpEndpoint]);

  const toolCountLabel = useMemo(
    () => `${MCP_TOOLS.length} tools · 0 prompts`,
    [],
  );

  const handleCopy = useCallback(async (kind: 'config' | 'verify') => {
    try {
      await navigator.clipboard.writeText(kind === 'config' ? mcpConfig : verifySnippet);
      setCopied(kind);
      setTimeout(() => setCopied(null), 1600);
    } catch {
      setCopied(null);
    }
  }, [mcpConfig, verifySnippet]);

  return (
    <section className={styles.section} aria-labelledby="mcp-heading">
      {/* ── MCP config ───────────────────────────────────── */}
      <header className={styles.head}>
        <h2 id="mcp-heading" className={styles.title}>{t('mcp.title')}</h2>
        <p className={styles.subtitle}>{t('mcp.subtitle')}</p>
      </header>

      <div className={styles.codeCard}>
        <div className={styles.codeBar}>
          <span className={styles.codeBarLabel}>mcp.json</span>
          <button
            type="button"
            className={styles.copyBtn}
            onClick={() => handleCopy('config')}
            aria-label={t('mcp.copy')}
          >
            {copied === 'config' ? t('mcp.copied') : t('mcp.copy')}
          </button>
        </div>
        <pre className={styles.code}>
          <code>{mcpConfig}</code>
        </pre>
      </div>

      {/* ── Server card with tool chips ──────────────────── */}
      <div className={styles.serverCard}>
        <div className={styles.serverHead}>
          <button
            type="button"
            className={styles.chevron}
            onClick={() => setExpanded(v => !v)}
            aria-expanded={expanded}
            aria-controls="mcp-tool-list"
            aria-label={expanded ? t('mcp.collapse') : t('mcp.expand')}
          >
            <svg
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              className={expanded ? styles.chevronOpen : ''}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <div className={styles.serverMeta}>
            <div className={styles.serverTitleRow}>
              <span className={styles.serverName}>{MCP_SERVER_NAME}</span>
              <span className={styles.scopeTag}>{t('mcp.scopeUser')}</span>
              <span className={styles.statusDot} title={t('mcp.connected')} />
            </div>
            <p className={styles.serverCount}>{toolCountLabel}</p>
          </div>

          <span className={styles.authTag}>{t('mcp.authPassthrough')}</span>
        </div>

        {expanded && (
          <ul id="mcp-tool-list" className={styles.chipList}>
            {MCP_TOOLS.map(tool => (
              <li key={tool.name} className={styles.chipItem}>
                <div className={styles.chipRow}>
                  <span className={styles.chip}>{tool.name}</span>
                  {tool.autoRegistered && (
                    <span className={styles.autoTag}>{t('mcp.autoRegistered')}</span>
                  )}
                </div>
                <code className={styles.chipRoute}>{tool.route}</code>
                <p className={styles.chipDesc}>{t(tool.descKey)}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── Auto-registration explainer + verify snippet ── */}
      <header className={styles.head}>
        <h3 className={styles.subTitle}>{t('mcp.verify.title')}</h3>
        <p className={styles.subtitle}>{t('mcp.verify.subtitle')}</p>
      </header>

      <div className={styles.codeCard}>
        <div className={styles.codeBar}>
          <span className={styles.codeBarLabel}>verify.sh</span>
          <button
            type="button"
            className={styles.copyBtn}
            onClick={() => handleCopy('verify')}
            aria-label={t('mcp.copy')}
          >
            {copied === 'verify' ? t('mcp.copied') : t('mcp.copy')}
          </button>
        </div>
        <pre className={styles.code}>
          <code>{verifySnippet}</code>
        </pre>
      </div>

      <p className={styles.note}>{t('mcp.verify.note')}</p>
    </section>
  );
}
