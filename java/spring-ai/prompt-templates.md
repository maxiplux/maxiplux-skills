# Spring AI Prompt Template Externalization Reference

## Overview

Externalizing prompts into resource files separates prompt content from Java logic, enabling:
- Non-developers to iterate on prompt text
- Version control of prompt changes independent of code
- Reuse across multiple services/endpoints
- Cleaner, more maintainable code

## File organization

```
src/main/resources/
└── prompts/
    ├── system/
    │   ├── default-system.st
    │   ├── analyst-persona.st
    │   └── tutor-persona.st
    └── user/
        ├── summarize.st
        ├── classify.st
        ├── extract-entities.st
        └── generate-report.st
```

Use `.st` extension (StringTemplate convention). Any text file works, but `.st` signals intent.

## Loading prompts with @Value injection

### System prompt from file

**`src/main/resources/prompts/system/default-system.st`**:
```
You are a helpful AI assistant. Your name is {name}.
Reply in the style of a {voice}.
```

**Java code**:
```java
@RestController
@RequiredArgsConstructor
public class ChatController {

    private final ChatModel chatModel;

    @Value("classpath:/prompts/system/default-system.st")
    private Resource systemResource;

    @GetMapping("/chat")
    public String chat(@RequestParam String question, @RequestParam String name) {
        SystemPromptTemplate systemTemplate = new SystemPromptTemplate(systemResource);
        Message systemMessage = systemTemplate.createMessage(
            Map.of("name", name, "voice", "a pirate"));

        Message userMessage = new UserMessage(question);
        Prompt prompt = new Prompt(List.of(userMessage, systemMessage));
        return chatModel.call(prompt).getResult().getOutput().getContent();
    }
}
```

### User prompt from file

**`src/main/resources/prompts/user/youtube-script.st`**:
```
You are an expert YouTuber. Write a script about {techStack}.
Target audience: {audience}. Tone: Energetic and encouraging.
```

```java
@Value("classpath:/prompts/user/youtube-script.st")
private Resource scriptResource;

public String generateScript(String techStack, String audience) {
    PromptTemplate template = new PromptTemplate(scriptResource);
    Prompt prompt = template.create(Map.of(
        "techStack", techStack, "audience", audience));
    return chatModel.call(prompt).getResult().getOutput().getContent();
}
```

## ChatClient.Builder with ClassPathResource — the modern approach

The `ChatClient.Builder` accepts `Resource` objects directly, providing the cleanest integration:

### Configuration bean

```java
@Configuration
public class AiConfig {

    @Bean
    ChatClient chatClient(ChatClient.Builder builder) {
        return builder
            .defaultSystem(new ClassPathResource("prompts/system/default-system.st"))
            .build();
    }
}
```

### Usage at call time

```java
@Service
@RequiredArgsConstructor
public class TaskAnalysisService {

    private final ChatClient chatClient;

    public String analyzeTask(String question, List<Task> tasks) {
        return chatClient.prompt()
            .system(sp -> sp.param("name", "Assistant"))
            .user(new ClassPathResource("prompts/user/analyze-tasks.st"))
            .user(spec -> spec
                .param("tasks", tasks)
                .param("question", question)
                .param("date", LocalDate.now()))
            .call()
            .content();
    }
}
```

### Builder overloads for defaultUser() and defaultSystem()

| Method signature | Description |
|-----------------|-------------|
| `defaultSystem(String text)` | Inline string template |
| `defaultSystem(Resource resource)` | Load from classpath resource |
| `defaultSystem(Resource resource, Charset charset)` | Load with specific encoding |
| `defaultSystem(Consumer<PromptSystemSpec>)` | Programmatic configuration |
| `defaultUser(String text)` | Inline string template |
| `defaultUser(Resource resource)` | Load from classpath resource |

Spring Boot auto-configures the `ChatClient.Builder` bean when a ChatModel starter is on the classpath.

## Variable substitution with StringTemplate v4

Spring AI uses **StringTemplate v4** (by Terence Parr) as the default engine via `StTemplateRenderer`. Variables use `{variableName}` syntax.

### Simple variables

```
Summarize the following text in {language}:
{content}
```

```java
chatClient.prompt()
    .user(new ClassPathResource("prompts/user/summarize.st"))
    .user(spec -> spec
        .param("language", "Spanish")
        .param("content", documentText))
    .call()
    .content();
```

### Iterating over objects

```
Tasks to analyze:
{tasks:{task|
- Task:
    - ID: {task.id}
    - Description: {task.description}
    - Due Date: {task.dueDate}
}}
```

Advanced iteration requires `ValidationMode.NONE`:

```java
StTemplateRenderer.builder()
    .validationMode(ValidationMode.NONE)
    .build();
```

### JSON in prompts — delimiter conflicts

Default `{` `}` delimiters conflict with JSON curly braces. Switch to angle-bracket delimiters:

```java
@Bean
ChatClient chatClient(ChatClient.Builder builder) {
    return builder
        .defaultTemplateRenderer(StTemplateRenderer.builder()
            .startDelimiterToken('<')
            .endDelimiterToken('>')
            .build())
        .defaultSystem(new ClassPathResource("prompts/system/default-system.st"))
        .build();
}
```

Then templates use `<variable>` instead of `{variable}`:

```
Respond with JSON matching this schema:
{"name": "<string>", "score": <number>}

Analyze: <content>
```

### Custom template engine

The `TemplateRenderer` interface (`BiFunction<String, Map<String, Object>, String>`) is pluggable. You can implement a custom renderer backed by Mustache, Thymeleaf, or any engine. A `NoOpTemplateRenderer` is available when no substitution is needed.

## Combining prompts with structured output

A common production pattern: externalized prompt + structured output converter:

**`src/main/resources/prompts/user/extract-entities.st`**:
```
Extract all named entities from the following text.
Categorize each as PERSON, ORGANIZATION, or LOCATION.

Text: {content}

{format}
```

```java
record NamedEntity(
    @JsonPropertyDescription("The entity name as it appears in the text")
    String name,
    @JsonPropertyDescription("Category: PERSON, ORGANIZATION, or LOCATION")
    String category
) {}

record EntityExtractionResult(List<NamedEntity> entities) {}

@Value("classpath:/prompts/user/extract-entities.st")
private Resource extractPrompt;

public EntityExtractionResult extractEntities(String content) {
    BeanOutputConverter<EntityExtractionResult> converter =
        new BeanOutputConverter<>(EntityExtractionResult.class);

    PromptTemplate template = new PromptTemplate(extractPrompt);
    Prompt prompt = template.create(Map.of(
        "content", content,
        "format", converter.getFormat()));

    Generation generation = chatModel.call(prompt).getResult();
    return converter.convert(generation.getOutput().getText());
}
```

Or more concisely with `ChatClient`:

```java
public EntityExtractionResult extractEntities(String content) {
    return chatClient.prompt()
        .user(new ClassPathResource("prompts/user/extract-entities-simple.st"))
        .user(spec -> spec.param("content", content))
        .call()
        .entity(EntityExtractionResult.class);
}
```

## Best practices checklist

1. **Organize prompts by role** — `prompts/system/` and `prompts/user/` directories
2. **Use `.st` extension** — signals StringTemplate usage to the team
3. **Prefer `ChatClient.Builder` with `ClassPathResource`** over `@Value` injection for cleaner config
4. **Switch to `<>` delimiters** when prompts contain JSON
5. **Keep prompts focused** — one file per intent (summarize, classify, extract, etc.)
6. **Version prompts with code** — they live in `src/main/resources`, tracked by Git
7. **Use `ValidationMode.NONE`** only when using advanced StringTemplate features (loops, nested access)
8. **Never hardcode prompts as Java string literals** in production code
9. **Document template variables** with comments at the top of `.st` files:
   ```
   // Variables: {content} - the text to analyze, {language} - target language
   Summarize the following text in {language}:
   {content}
   ```
10. **Test prompts independently** — validate variable substitution in unit tests before integration testing with an LLM
