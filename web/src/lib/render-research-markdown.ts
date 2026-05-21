/**
 * Render a research findings.md body to HTML.
 *
 * Mirrors src/dilemmas/api/research_parser.py:render_markdown:
 *   - strips the first H1 (page already has the title from the layout)
 *   - rewrites relative image paths `figures/x.png` →
 *     `/research-static/{slug}/figures/x.png` so the same markdown renders
 *     correctly on GitHub (relative) and on research.values.md (absolute)
 *   - GFM enabled (tables, strikethrough, autolinks)
 */
import { marked } from 'marked';
import { gfmHeadingId } from 'marked-gfm-heading-id';

marked.use(gfmHeadingId());
marked.setOptions({ gfm: true, breaks: false });

export interface RenderOptions {
  slug?: string;
  stripFirstH1?: boolean;
}

export function renderResearchMarkdown(body: string, opts: RenderOptions = {}): string {
  let md = body;

  if (opts.slug) {
    md = md.replace(
      /!\[([^\]]*)\]\((?!https?:|\/)([^)]+)\)/g,
      (_m, alt, path) => `![${alt}](/research-static/${opts.slug}/${path})`,
    );
  }

  if (opts.stripFirstH1 !== false) {
    const lines = md.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i]!.trim();
      if (trimmed.startsWith('# ')) {
        lines.splice(i, 1);
        break;
      }
      if (trimmed) break;
    }
    md = lines.join('\n');
  }

  // Defensive: ensure a blank line before any list item that isn't preceded by one.
  // python-markdown's `sane_lists` extension is forgiving in a way GFM isn't.
  md = md.replace(
    /([^\n])\n((?:- |\* |\+ |\d+\. ))/g,
    (_m, prev, marker) => `${prev}\n\n${marker}`,
  );

  return marked.parse(md, { async: false }) as string;
}
