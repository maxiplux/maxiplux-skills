---
name: spring-boot-ai
description: >
  Comprehensive Spring Boot and Spring AI development skill covering structured output conversion,
  prompt template externalization, and production-grade Spring Boot patterns. Use this skill whenever
  working on Spring Boot projects, Spring AI integrations, REST API development with Spring, Spring Security
  configuration, Vertical Slices Architecture in Spring, database migrations with Flyway, rate limiting
  with Bucket4j, or any Java backend using Spring Framework. Also triggers for: ChatClient usage,
  BeanOutputConverter, PromptTemplate, Spring AI entity mapping, LLM response parsing, externalized
  prompts, Spring Boot testing strategies, exception handling patterns, logging standards, or any
  task involving spring-ai, spring-boot-starter, or Spring MVC. If the user mentions Spring, Spring Boot,
  Spring AI, Spring Security, or any Spring ecosystem library, consult this skill.
---

# Spring Boot & Spring AI Development Skill

This skill provides production-grade patterns for Spring Boot backend development and Spring AI integration. It covers three domains organized as reference files — read the relevant one(s) based on the task.

## When to read which reference

| Task | Reference file to read |
|------|----------------------|
| Mapping LLM responses to Java objects, using `.entity()`, converters, JSON schema | `references/structured-output.md` |
| Externalizing prompts to files, `PromptTemplate`, `SystemPromptTemplate`, variable substitution | `references/prompt-templates.md` |
| Spring Boot architecture, security, testing, logging, exception handling, API design | `references/spring-boot-patterns.md` |

Read multiple references when the task spans domains (e.g., building a Spring AI endpoint needs both structured-output and spring-boot-patterns).

## Core principles

These principles apply across all three reference files:

1. **Always use Spring Web MVC (servlet/Tomcat)** — never WebFlux or reactive stack.
2. **Vertical Slices Architecture (VSA)** — organize code under `features/`, one handler per use case. Subfolders: `api/request/`, `api/response/`, `handlers/`, `model/`, `enums/`, `exception/`.
3. **Records over classes** for DTOs, requests, responses, and AI structured output types.
4. **Secrets as environment variables** — never in `application.properties` or committed to source.
5. **Flyway for all schema changes** — no manual DDL.
6. **`@Slf4j` with structured key-value logging** — tiered log levels (ERROR for failures, WARN for degraded, INFO for business events, DEBUG for internals).
7. **Spring AI ChatClient as primary API** — prefer the fluent `ChatClient` API over raw `ChatModel` calls.
