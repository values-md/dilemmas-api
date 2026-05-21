/**
 * Astro content collections. The `research` collection points at
 * ../research/<slug>/findings.md (canonical location, also read by the
 * Python analysis scripts). Frontmatter is Zod-validated.
 *
 * Image references in the body use relative paths (figures/x.png) so they
 * also render correctly on GitHub. They're rewritten to /research-static/{slug}/figures/x.png
 * at render time by src/lib/render-research-markdown.ts.
 */
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const research = defineCollection({
  loader: glob({
    pattern: '*/findings.md',
    base: '../research',
    // Use the parent directory name (the date-slug) as the entry ID.
    // Some findings.md have a `slug:` field, some don't — without this,
    // the default path-derived ID would be `<slug>/findings` for the
    // ones without an explicit slug, breaking [slug].astro routing.
    generateId: ({ entry }) => entry.split('/')[0]!,
  }),
  schema: z.object({
    title: z.string(),
    date: z.union([z.string(), z.date()]).transform((v) => (v instanceof Date ? v.toISOString().slice(0, 10) : v)),
    status: z.enum(['completed', 'in_progress']).optional().default('completed'),
    experiment_id: z.string().optional(),
    version: z.union([z.string(), z.number()]).optional(),
    slug: z.string().optional(),
    og_image: z.string().optional(),
    og_image_alt: z.string().optional(),
    abstract: z.string().optional(),
    key_finding: z.string().optional(),
    research_question: z.string().optional(),
    hypothesis: z.string().optional(),
    models: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    data: z
      .object({
        dilemmas: z.number().optional(),
        judgements: z.number().optional(),
        conditions: z.number().optional(),
      })
      .partial()
      .optional(),
  }).passthrough(),
});

export const collections = { research };
