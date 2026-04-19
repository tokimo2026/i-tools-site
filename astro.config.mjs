// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://tokimo2026.github.io',
  base: '/i-tools-site',
  integrations: [sitemap()],
});
