# maxiplux-skills

A curated collection of AI coding-agent skills for personal and professional projects. Each skill is a structured knowledge package that helps AI assistants follow production-grade patterns when working on specific technology stacks.

---

## Repository Structure

```
maxiplux-skills/
├── java/
│   ├── spring-ai/          # Spring Boot + Spring AI skill
│   └── spring-boot-vsa/    # Spring Boot Vertical Slice Architecture skill
└── README.md
```

---

## Available Skills

### 1. `spring-boot-ai` — Spring Boot & Spring AI

**Location:** `java/spring-ai/`

Covers production-grade patterns for Spring Boot backend development and Spring AI integration. Topics include structured output conversion (mapping LLM responses to Java objects), prompt template externalization, Spring Boot architecture, security, testing, logging, and exception handling.

**Key files:**

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill manifest — describes the skill and when to use it |
| `spring-boot-ai.skill` | Packaged skill bundle (ZIP) for direct import into AI tools |
| `spring-boot-patterns.md` | Spring Boot architecture, testing, security, logging, API design patterns |
| `structured-output.md` | Mapping LLM responses to Java objects via `BeanOutputConverter` |
| `prompt-templates.md` | Externalizing prompts with `PromptTemplate` / `SystemPromptTemplate` |

---

### 2. `spring-boot-vsa` — Spring Boot Vertical Slice Architecture

**Location:** `java/spring-boot-vsa/`

An architectural guideline for organizing Spring Boot projects by Vertical Slice Architecture (VSA). Covers scaffolding new feature slices, auditing existing code for VSA violations, and refactoring layered projects into slices.

**Key files:**

| File | Purpose |
|------|---------|
| `SKILL.md` | Full VSA specification — package layout, naming conventions, cross-cutting rules |
| `scripts/create_slice.py` | CLI script to scaffold a new feature slice from templates |
| `assets/*.tmpl` | Java file templates used by the scaffolding script |
| `references/basic-crud-slice.md` | Worked example: complete CRUD slice |
| `references/event-driven-slice.md` | Worked example: slice with domain events + async listener |
| `references/external-api-slice.md` | Worked example: slice with `@Retryable` external API call + `@Recover` fallback |

---

## How to Install a Skill

Skills in this repository are designed to be used with **AI coding agents** (e.g. Claude, GitHub Copilot, Cursor). There are two ways to install them depending on your tool.

### Option A — Import the `.skill` bundle (recommended)

The `.skill` files are pre-packaged bundles ready for direct import.

1. Clone or download this repository:
2.    ```bash
         git clone https://github.com/maxiplux/maxiplux-skills.git
         ```

      2. Locate the `.skill` file for the skill you want, for example:
      3.    ```
               java/spring-ai/spring-boot-ai.skill
               ```

            3. Import it into your AI tool using that tool's skill/knowledge-import feature.
        
            4. ---
        
            5. ### Option B — Point your AI agent at the `SKILL.md` file
        
            6. If your AI tool supports referencing files or URLs directly (e.g. via a system prompt or context file), you can point it at the `SKILL.md` for the skill you want:
        
            7. - Spring Boot + Spring AI: `java/spring-ai/SKILL.md`
               - - Spring Boot VSA: `java/spring-boot-vsa/SKILL.md`
                
                 - The `SKILL.md` contains the full skill specification including the `name`, `description`, and all reference material the agent needs.
                
                 - ---

                 ### Option C — Use the VSA scaffolding script directly

                 The `spring-boot-vsa` skill ships with a Python scaffolding script you can run locally in any Spring Boot project.

                 **Prerequisites:** Python 3.8+

                 1. Copy the `java/spring-boot-vsa/` directory into your project (or reference it in place):
                 2.    ```bash
                          cp -r java/spring-boot-vsa/ /path/to/your/project/skills/spring-boot-vsa/
                          ```

                       2. Run the scaffolding script to generate a new feature slice:
                       3.    ```bash
                                python skills/spring-boot-vsa/scripts/create_slice.py \
                                  --feature payment \
                                  --actions create,list,get,update,delete \
                                  --base-package com.example.myapp \
                                  --output-dir src/main/java
                                ```

                                | Argument | Description | Example |
                            |----------|-------------|---------|
                            | `--feature` | Feature name (single lowercase noun) | `payment` |
                            | `--actions` | Comma-separated use cases to scaffold | `create,list,get,update,delete` |
                            | `--base-package` | Java base package of your application | `com.example.myapp` |
                            | `--output-dir` | Root directory where source files are generated | `src/main/java` |

                         3. The script generates the full slice directory under:
                         4.    ```
                                  src/main/java/com/example/myapp/features/payment/
                                  ├── api/
                                  │   ├── PaymentController.java
                                  │   ├── request/
                                  │   └── response/
                                  ├── handlers/
                                  ├── model/
                                  ├── enums/
                                  └── exception/
                                  ```

                               4. Fill in the generated placeholder logic (entity fields, handler business logic, mapper, repository queries).
                           
                               5. ---
                           
                               6. ## Contributing
                           
                               7. To add a new skill:
                           
                               8. 1. Create a directory under the appropriate language folder (e.g. `java/my-new-skill/`).
                                  2. 2. Add a `SKILL.md` with `name` and `description` front matter, followed by the full skill specification.
                                     3. 3. Optionally package it into a `.skill` bundle and add any reference markdown files.
                                        4. 4. Update this README with an entry in the **Available Skills** section.
                                          
                                           5. ---
                                          
                                           6. ## License
                                          
                                           7. MIT
