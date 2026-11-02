/**
 * "Ask AI" deep links (Option A): the app never calls an AI service itself. It opens the
 * chosen assistant in a new tab with a ready-made question, so no API key is needed and no
 * LLM output ever feeds a prediction.
 */

export type ResearchProvider = 'perplexity' | 'chatgpt' | 'gemini';
export type ResearchMode = 'search' | 'project';

export interface ResearchConfig {
  provider: ResearchProvider;
  mode: ResearchMode;
  /** Project / space URL per provider, used when mode is 'project'. */
  projectUrls: Record<ResearchProvider, string>;
}

interface ProviderMeta {
  label: string;
  /** Hosts a project URL must belong to. */
  hosts: string[];
  /** Builds a pre-filled new-chat URL, or null when the site has no prefill parameter. */
  searchUrl: (prompt: string) => string | null;
  homeUrl: string;
}

export const PROVIDERS: Record<ResearchProvider, ProviderMeta> = {
  perplexity: {
    label: 'Perplexity',
    hosts: ['www.perplexity.ai', 'perplexity.ai'],
    searchUrl: (q) => `https://www.perplexity.ai/search?q=${encodeURIComponent(q)}`,
    homeUrl: 'https://www.perplexity.ai/',
  },
  chatgpt: {
    label: 'ChatGPT',
    hosts: ['chatgpt.com'],
    searchUrl: (q) => `https://chatgpt.com/?q=${encodeURIComponent(q)}`,
    homeUrl: 'https://chatgpt.com/',
  },
  gemini: {
    label: 'Gemini',
    hosts: ['gemini.google.com'],
    searchUrl: () => null, // Gemini has no prefill parameter: the prompt is copied instead
    homeUrl: 'https://gemini.google.com/app',
  },
};

export const DEFAULT_CONFIG: ResearchConfig = {
  provider: 'perplexity',
  mode: 'project',
  projectUrls: {
    perplexity: 'https://www.perplexity.ai/projects/33433304-bb76-4c17-bae4-9d027602e780',
    chatgpt: '',
    gemini: '',
  },
};

export const PRESETS = [
  {
    id: 'trends',
    label: 'News & trends',
    prompt: (s: string) =>
      `${s} (NSE India): summarise the news, price trend and analyst sentiment of the last 30 days. Cite sources.`,
  },
  {
    id: 'sector',
    label: 'Sector outlook',
    prompt: (s: string) =>
      `${s} (NSE India): what is the outlook for its sector over the next 6–12 months, and how is it positioned against peers? Cite sources.`,
  },
  {
    id: 'risks',
    label: 'Risks & events',
    prompt: (s: string) =>
      `${s} (NSE India): list the main risks and upcoming events (results, regulation, corporate actions). Cite sources.`,
  },
] as const;

/** True when the URL is https and on the provider's own site. */
export function isValidProjectUrl(provider: ResearchProvider, url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && PROVIDERS[provider].hosts.includes(parsed.hostname);
  } catch {
    return false;
  }
}

export interface ResearchLaunch {
  url: string;
  /** True when the prompt cannot be pre-filled and must be pasted by the user. */
  needsPaste: boolean;
}

/** Where to go for a prompt: a pre-filled search, or the project page plus a paste. */
export function buildLaunch(config: ResearchConfig, prompt: string): ResearchLaunch {
  const meta = PROVIDERS[config.provider];
  const projectUrl = config.projectUrls[config.provider];
  if (config.mode === 'project' && isValidProjectUrl(config.provider, projectUrl)) {
    return { url: projectUrl, needsPaste: true };
  }
  const search = meta.searchUrl(prompt);
  return search ? { url: search, needsPaste: false } : { url: meta.homeUrl, needsPaste: true };
}

const STORAGE_KEY = 'sa.ai-research';

export function readConfig(): ResearchConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_CONFIG;
    const saved = JSON.parse(raw) as Partial<ResearchConfig>;
    return {
      ...DEFAULT_CONFIG,
      ...saved,
      projectUrls: { ...DEFAULT_CONFIG.projectUrls, ...saved.projectUrls },
    };
  } catch {
    return DEFAULT_CONFIG; // storage blocked or corrupt: use defaults
  }
}

export function writeConfig(config: ResearchConfig): boolean {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    return true;
  } catch {
    return false;
  }
}
