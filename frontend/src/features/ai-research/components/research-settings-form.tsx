import { useState } from 'react';
import { toast } from 'sonner';

import {
  isValidProjectUrl,
  PROVIDERS,
  readConfig,
  writeConfig,
  type ResearchMode,
  type ResearchProvider,
} from '../lib/research-config';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group';

const PROVIDER_KEYS = Object.keys(PROVIDERS) as ResearchProvider[];

/** Which assistant "Ask AI" opens, and whether it opens a direct search or your project. */
export function ResearchSettingsForm() {
  const [config, setConfig] = useState(readConfig);
  const projectUrl = config.projectUrls[config.provider];
  const isUrlInvalid =
    config.mode === 'project' &&
    projectUrl !== '' &&
    !isValidProjectUrl(config.provider, projectUrl);

  const save = () => {
    if (writeConfig(config)) toast.success('AI research settings saved');
    else toast.error('This browser blocks local storage, so the settings could not be saved.');
  };

  return (
    <form
      className="flex max-w-xl flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        save();
      }}
    >
      <div className="flex flex-col gap-2">
        <Label>Assistant</Label>
        <ToggleGroup
          value={[config.provider]}
          onValueChange={(value: string[]) => {
            const next = value[0] as ResearchProvider | undefined;
            if (next) setConfig({ ...config, provider: next });
          }}
          aria-label="Assistant"
        >
          {PROVIDER_KEYS.map((key) => (
            <ToggleGroupItem key={key} value={key}>
              {PROVIDERS[key].label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Open as</Label>
        <ToggleGroup
          value={[config.mode]}
          onValueChange={(value: string[]) => {
            const next = value[0] as ResearchMode | undefined;
            if (next) setConfig({ ...config, mode: next });
          }}
          aria-label="Open as"
        >
          <ToggleGroupItem value="search">Direct search</ToggleGroupItem>
          <ToggleGroupItem value="project">Under a project</ToggleGroupItem>
        </ToggleGroup>
        <p className="text-xs text-muted-foreground">
          {config.mode === 'search'
            ? config.provider === 'gemini'
              ? 'Gemini cannot pre-fill a question: it opens and the question is copied for you to paste.'
              : 'Opens a new chat with the question already filled in.'
            : 'Opens your project and copies the question for you to paste, so the answer is saved there.'}
        </p>
      </div>
      {config.mode === 'project' && (
        <div className="flex flex-col gap-2">
          <Label htmlFor="project-url">{PROVIDERS[config.provider].label} project URL</Label>
          <Input
            id="project-url"
            type="url"
            placeholder={`${PROVIDERS[config.provider].homeUrl}…`}
            value={projectUrl}
            aria-invalid={isUrlInvalid}
            onChange={(e) => {
              setConfig({
                ...config,
                projectUrls: { ...config.projectUrls, [config.provider]: e.target.value.trim() },
              });
            }}
          />
          <p className="text-xs text-muted-foreground">
            {isUrlInvalid
              ? `Must be an https link on ${PROVIDERS[config.provider].hosts[0] ?? ''}.`
              : 'Empty: falls back to a direct search.'}
          </p>
        </div>
      )}
      <div>
        <Button type="submit" disabled={isUrlInvalid}>
          Save
        </Button>
      </div>
    </form>
  );
}
