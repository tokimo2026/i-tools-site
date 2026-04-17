const fs = require('fs');
const path = require('path');

const srcDir = '/Users/komatsutomoki/Library/Application Support/Claude/ai-tools-site-v4/articles';
const outDir = path.join(__dirname, 'src/content/articles');

const files = fs.readdirSync(srcDir).filter(f => f.endsWith('.html'));

for (const file of files) {
  const html = fs.readFileSync(path.join(srcDir, file), 'utf-8');
  const slug = file.replace('.html', '');

  // Extract title
  const titleMatch = html.match(/<title>([^<]+?)(?:\s*-\s*AI実践ラボ)?<\/title>/);
  const title = titleMatch ? titleMatch[1].trim() : slug;

  // Extract description
  const descMatch = html.match(/<meta name="description" content="([^"]+)"/);
  const description = descMatch ? descMatch[1] : title;

  // Extract date
  const dateMatch = html.match(/"datePublished":\s*"([^"]+)"/);
  const date = dateMatch ? dateMatch[1] : '2026-04-10';

  // Extract category from breadcrumb or article-category
  const catMatch = html.match(/<span class="article-category">([^<]+)<\/span>/);
  const category = catMatch ? catMatch[1] : 'AI';

  // Extract main article content between <article class="article-body"> sections
  // Get content after </h1> and before <!-- 関連記事 --> or </article>
  let content = '';

  // Find all <section> blocks
  const sectionRegex = /<section[^>]*>([\s\S]*?)<\/section>/g;
  let match;
  const sections = [];
  while ((match = sectionRegex.exec(html)) !== null) {
    sections.push(match[1]);
  }

  for (const section of sections) {
    let md = section
      // Remove HTML tags but keep structure
      .replace(/<h2[^>]*>/g, '\n## ')
      .replace(/<\/h2>/g, '\n')
      .replace(/<h3[^>]*>/g, '\n### ')
      .replace(/<\/h3>/g, '\n')
      .replace(/<p[^>]*>/g, '\n')
      .replace(/<\/p>/g, '\n')
      .replace(/<strong>/g, '**')
      .replace(/<\/strong>/g, '**')
      .replace(/<code>/g, '`')
      .replace(/<\/code>/g, '`')
      .replace(/<li>/g, '- ')
      .replace(/<\/li>/g, '\n')
      .replace(/<br\s*\/?>/g, '\n')
      // Remove remaining HTML tags
      .replace(/<[^>]+>/g, '')
      // Clean up whitespace
      .replace(/\n{3,}/g, '\n\n')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .trim();

    if (md.length > 10) {
      content += md + '\n\n';
    }
  }

  // Build frontmatter
  const frontmatter = `---
title: "${title.replace(/"/g, '\\"')}"
description: "${description.replace(/"/g, '\\"')}"
category: "${category}"
date: "${date}"
layout: ../../layouts/ArticleLayout.astro
---`;

  const markdown = frontmatter + '\n\n' + content.trim() + '\n';

  fs.writeFileSync(path.join(outDir, slug + '.md'), markdown);
  console.log(`Converted: ${file} -> ${slug}.md (${content.length} chars)`);
}

console.log(`\nDone. ${files.length} articles converted.`);
