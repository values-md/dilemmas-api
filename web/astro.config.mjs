import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'server',
  adapter: cloudflare({
    imageService: 'compile',
    platformProxy: { enabled: true },
  }),
  site: 'https://research.values.md',
  // Match Python's URL shape: /research/<slug>, no trailing slash, no .html
  trailingSlash: 'never',
  build: { format: 'file' },
  vite: {
    resolve: {
      alias: import.meta.env.PROD
        ? { 'react-dom/server': 'react-dom/server.edge' }
        : {},
    },
  },
});
