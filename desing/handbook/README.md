# Visual handbook renderer

Read the [published handbook](https://maxiplux.github.io/maxiplux-skills-handbook/), or open [guide-lines.html](../guide-lines.html) in a browser. Its reading content, images, styles, and interactions are self-contained and work offline; readers do not need Node or a web server. External references need internet access, and links to source files need the repository or published site.

The source index is [guide-lines](../guide-lines). Edit the three chapter sources: [UI / UX & Design](../ui-ux-design.md), [AI Agents](../ai-agents.md), and [Software Architecture](../software-architecture.md). The browser shell supplies interactive examples, grouped navigation, image enlargement, and copy controls. Images live in [assets](../assets).

To regenerate after an edit, from this directory:

```sh
npm ci
npm run build
```

## Publish on GitHub Pages

The live handbook is hosted in the public [maxiplux-skills-handbook repository](https://github.com/maxiplux/maxiplux-skills-handbook). This authoring repository remains private.

To prepare the public copy, run `npm run build:public` from this directory. Copy only the contents of the generated `_public-site/` directory into the hosting repository, commit, and push to `main`. GitHub Pages publishes that branch's root automatically. The bundle includes two HTML editions and the SVG/JSON illustration resources linked by the guide. Implementation-source links point back to this private repository; source files, installers, and Git history are not copied.

The workflow in this authoring repository validates changes and uploads an artifact. It does not automatically push to the separate hosting repository.

### Build the complete site from this repository

From this directory, run:

```sh
npm ci
npm run build:pages
```

This rebuilds the offline document and prepares the ignored [_site/](../../_site/) directory. The site opens the handbook at its root and retains the offline download at `desing/guide-lines.html`. Relative source links are adjusted for the root page, so both versions work under a GitHub project URL. The build checks local Markdown links, HTML anchors, image alternatives, and image dimensions. Run `npm run check` to repeat those checks on an existing build.

The publisher copies only the handbook resources, the three skills' documentation/scaffolding/templates, the two installers, this repository's README, and the Pages workflow. These are the resources linked by the guide. Local agent settings, dependencies, caches, and Git history are excluded. Files placed in the deployment artifact are publicly accessible even when the source repository is private.

In the repository's **Settings → Pages**, choose **GitHub Actions** as the source. The [Publish handbook workflow](../../.github/workflows/pages.yml) builds on relevant pushes to `main` or a manual run. Deployment runs for public repositories. For a private repository, first enable Pages on a supported GitHub plan, then set the Actions repository variable `PRIVATE_PAGES_ENABLED` to `true`. Until then, the build still uploads a downloadable site artifact and skips deployment.

For a local preview after building, run from the repository root:

```sh
python -m http.server 4173 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:4173/`. Keep the generated HTML committed when updating the sources so readers can also download the offline edition directly from the repository.

## Renderer and illustrations

The build compiles Tailwind CSS 4 and daisyUI 5, renders the three Markdown chapters, embeds local PNG and static SVG image data, and writes the browser document. It does not install the skills discussed in the guide. Dependencies are needed only to regenerate the document. New chapter sections must also have labels and IDs in [chapters.mjs](./chapters.mjs). Cross-links between chapter sources become anchors within the illustrated page.

The teaching illustrations were made with the built-in image generator. The newest prompts are in [expanded-image-prompts.json](../assets/expanded-image-prompts.json); earlier prompts remain in [blue-image-prompts.json](../assets/blue-image-prompts.json) and [image-prompts.json](../assets/image-prompts.json). The [VSA diagram](../assets/vsa-feature-slice.svg) and [Spring AI flow](../assets/spring-ai-data-flow.svg) are editable SVG sources. The form lifecycle, agent control loop, request flow and complete-feature diagrams are regenerated from [diagrams.mjs](./diagrams.mjs); edit that generator to preserve changes across builds. Illustrations teach concepts and contain fictional examples, not evidence of actual tests.

The picker, API-state demo and expanded details preserve their state in URL parameters where the browser permits local-file history updates. The image viewer uses a native dialog with keyboard dismissal and focus return. Printing shows all chapter text and expands details.
