import { ExternalLink, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import { buildLaunch, PRESETS, PROVIDERS, readConfig } from '../lib/research-config';
import { Button } from '@/shared/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';

/** Opens the assistant chosen in Settings with a ready-made question about the stock. */
export function AskAiButton({ symbol }: { symbol: string }) {
  const ask = async (prompt: string) => {
    const config = readConfig();
    const label = PROVIDERS[config.provider].label;
    const launch = buildLaunch(config, prompt);
    // open first: browsers only allow pop-ups straight from the click
    window.open(launch.url, '_blank', 'noopener,noreferrer');
    if (!launch.needsPaste) return;
    try {
      await navigator.clipboard.writeText(prompt);
      toast.success(`Question copied. Paste it into ${label}.`);
    } catch {
      toast.info(`Paste this into ${label}: ${prompt}`, { duration: 15_000 });
    }
  };
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" size="lg">
            <Sparkles aria-hidden="true" />
            Ask AI
          </Button>
        }
      />
      <DropdownMenuContent align="end" className="w-56">
        {/* Base UI: a menu label must sit inside a group, or the page crashes on open. */}
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            Opens {PROVIDERS[readConfig().provider].label} in a new tab
          </DropdownMenuLabel>
          {PRESETS.map((preset) => (
            <DropdownMenuItem
              key={preset.id}
              onClick={() => {
                void ask(preset.prompt(symbol));
              }}
            >
              {preset.label}
              <ExternalLink className="ml-auto" aria-hidden="true" />
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
