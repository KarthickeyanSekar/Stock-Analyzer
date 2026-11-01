// UI rule check (CLAUDE.md "Frontend UI rules", docs/24 section 6b), run by `npm run lint`.
// Feature code must use design tokens, Lucide icons and shadcn components: this fails on
// raw Tailwind palette colours, hex colours, emoji and native <select> in app/, pages/, features/.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOTS = ['src/app', 'src/pages', 'src/features'];
const RULES = [
  {
    name: 'raw palette colour (use a token: bg-card, text-muted-foreground, text-gain …)',
    pattern:
      /\b(?:bg|text|border|ring|fill|stroke|from|to|via|outline|divide)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/,
  },
  {
    name: 'hex colour (use a CSS variable token)',
    pattern: /#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?=['"\s;)])/,
  },
  { name: 'emoji (use a Lucide icon)', pattern: /\p{Extended_Pictographic}/u },
  { name: 'native <select> (use the shadcn Select)', pattern: /<select[\s>]/ },
];

const files = (dir) =>
  readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : /\.(tsx?|css)$/.test(name) ? [path] : [];
  });

const problems = [];
for (const file of ROOTS.flatMap(files)) {
  readFileSync(file, 'utf8')
    .split('\n')
    .forEach((line, index) => {
      if (line.includes('ui-rules-ignore')) return;
      for (const rule of RULES) {
        if (rule.pattern.test(line))
          problems.push(`${relative('.', file)}:${String(index + 1)}  ${rule.name}`);
      }
    });
}

if (problems.length > 0) {
  console.error(`UI rules: ${String(problems.length)} problem(s)\n${problems.join('\n')}`);
  process.exit(1);
}
console.log('UI rules: OK');
