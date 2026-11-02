import { describe, expect, it } from 'vitest';

import {
  buildLaunch,
  DEFAULT_CONFIG,
  isValidProjectUrl,
  type ResearchConfig,
} from './research-config';

const config = (patch: Partial<ResearchConfig>): ResearchConfig => ({
  ...DEFAULT_CONFIG,
  ...patch,
});

describe('buildLaunch', () => {
  it('pre-fills a Perplexity search', () => {
    const launch = buildLaunch(config({ mode: 'search' }), 'TCS trends');
    expect(launch).toEqual({
      url: 'https://www.perplexity.ai/search?q=TCS%20trends',
      needsPaste: false,
    });
  });

  it('opens the project page and asks for a paste in project mode', () => {
    const launch = buildLaunch(config({ mode: 'project' }), 'TCS trends');
    expect(launch.url).toBe(DEFAULT_CONFIG.projectUrls.perplexity);
    expect(launch.needsPaste).toBe(true);
  });

  it('falls back to search when the project URL is missing', () => {
    const launch = buildLaunch(config({ provider: 'chatgpt', mode: 'project' }), 'x');
    expect(launch).toEqual({ url: 'https://chatgpt.com/?q=x', needsPaste: false });
  });

  it('opens Gemini and asks for a paste because it has no prefill', () => {
    const launch = buildLaunch(config({ provider: 'gemini', mode: 'search' }), 'x');
    expect(launch).toEqual({ url: 'https://gemini.google.com/app', needsPaste: true });
  });
});

describe('isValidProjectUrl', () => {
  it('accepts only https links on the provider site', () => {
    expect(isValidProjectUrl('chatgpt', 'https://chatgpt.com/g/g-p-1/project')).toBe(true);
    expect(isValidProjectUrl('chatgpt', 'https://evil.example/chatgpt.com')).toBe(false);
    expect(isValidProjectUrl('perplexity', 'http://www.perplexity.ai/projects/1')).toBe(false);
    expect(isValidProjectUrl('gemini', 'not a url')).toBe(false);
  });
});
