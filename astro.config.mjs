// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://teal-bienenstitch-e337b8.netlify.app',
  integrations: [sitemap()],
});
