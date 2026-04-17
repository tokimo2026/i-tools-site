import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.string(),
    date: z.string(),
    layout: z.string().optional(),
    rating: z.string().optional(),
    price: z.string().optional(),
    difficulty: z.string().optional(),
    target: z.string().optional(),
    readTime: z.string().optional(),
  }),
});

export const collections = { articles };
