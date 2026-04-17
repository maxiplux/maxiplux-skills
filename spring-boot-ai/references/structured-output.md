# Spring AI Structured Output Reference

## Overview

Spring AI converts LLM text responses into typed Java objects through a two-phase system:
- **Before the call**: a `FormatProvider` generates JSON Schema instructions appended to the prompt
- **After the call**: a `Converter<String, T>` deserializes the raw response into the target type

Both behaviors are unified in `StructuredOutputConverter<T>`:

```java
public interface StructuredOutputConverter<T> extends Converter<String, T>, FormatProvider { }
```

## Built-in converters

| Converter | Purpose | Output type |
|-----------|---------|-------------|
| `BeanOutputConverter<T>` | Maps to Java records/classes via JSON Schema (DRAFT_2020_12) | `T` |
| `ListOutputConverter` | Comma-delimited list parsing | `List<String>` |
| `MapOutputConverter` | JSON to map parsing | `Map<String, Object>` |

## ChatClient `.entity()` — the recommended approach

The `ChatClient` fluent API handles converter creation, prompt augmentation, LLM call, and deserialization automatically:

### Simple bean mapping

```java
record ActorsFilms(String actor, List<String> movies) {}

ActorsFilms result = chatClient.prompt()
    .user(u -> u.text("Generate the filmography of 5 movies for {actor}.")
                .param("actor", "Tom Hanks"))
    .call()
    .entity(ActorsFilms.class);
```

### Generic types with ParameterizedTypeReference

```java
List<ActorsFilms> results = chatClient.prompt()
    .user("Generate filmographies for Tom Hanks and Bill Murray.")
    .call()
    .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});
```

### List output with ListOutputConverter

```java
List<String> flavors = chatClient.prompt()
    .user(u -> u.text("List five {subject}").param("subject", "ice cream flavors"))
    .call()
    .entity(new ListOutputConverter(new DefaultConversionService()));
```

### Getting entity + metadata together

Use `.responseEntity()` to get both the parsed entity and `ChatResponse` metadata (token usage, finish reason) in a single LLM call. Calling `.entity()` and `.chatResponse()` separately triggers two API calls.

```java
ChatClient.CallResponseSpec.ResponseEntity<ActorsFilms> response = chatClient.prompt()
    .user("Generate filmography for Tom Hanks")
    .call()
    .responseEntity(ActorsFilms.class);

ActorsFilms entity = response.entity();
ChatResponse chatResponse = response.response(); // token usage, finish reason, etc.
```

### `.entity()` overloads

| Signature | Use case |
|-----------|----------|
| `entity(Class<T>)` | Simple bean/record mapping |
| `entity(ParameterizedTypeReference<T>)` | Generic types like `List<T>`, `Map<K,V>` |
| `entity(StructuredOutputConverter<T>)` | Custom converter (e.g., `ListOutputConverter`) |

## Low-level ChatModel API

Use when you need fine-grained control over prompt construction or converter behavior:

```java
BeanOutputConverter<ActorsFilms> converter = new BeanOutputConverter<>(ActorsFilms.class);

String template = """
    Generate the filmography of 5 movies for {actor}.
    {format}
    """;

Generation generation = chatModel.call(
    PromptTemplate.builder()
        .template(template)
        .variables(Map.of("actor", "Tom Hanks", "format", converter.getFormat()))
        .build().create()
).getResult();

ActorsFilms result = converter.convert(generation.getOutput().getText());
```

The `{format}` placeholder is where `getFormat()` injects the JSON schema and RFC 8259 compliance instructions.

## Jackson annotations for schema enrichment

Spring AI uses standard Jackson annotations (not a custom `@Description`) to shape the JSON schema sent to the model:

```java
@JsonPropertyOrder({"firstName", "lastName", "years"})
public record ChessChampion(
    @JsonProperty(value = "firstName") String first,
    @JsonProperty(value = "lastName") String last,
    @JsonPropertyDescription("The years when they were world champions.")
    List<Integer> years
) {}
```

| Annotation | Effect on schema |
|-----------|-----------------|
| `@JsonPropertyDescription` | Adds `description` field — gives LLM semantic guidance |
| `@JsonProperty(required = true)` | Populates `required` array — essential for OpenAI strict mode |
| `@JsonPropertyOrder` | Controls property ordering in generated schema |
| `@JsonIgnore` | Excludes field from schema entirely |

The `@Description` annotation in Spring AI exists but is for **Tool Calling function beans**, not for structured output fields.

## Native structured output (model-level JSON schema)

Modern LLMs (OpenAI GPT-4o+, Claude 3.5+, Gemini 1.5 Pro+) support sending JSON schemas directly to the model's API rather than appending instructions to the prompt. This provides higher reliability and cleaner prompts:

### Per-call activation

```java
ActorsFilms result = chatClient.prompt()
    .advisors(AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT)
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class);
```

### Global default via ChatClient.Builder

```java
@Bean
ChatClient chatClient(ChatClient.Builder builder) {
    return builder
        .defaultAdvisors(AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT)
        .build();
}
```

**Limitation**: Some models (notably OpenAI) do not support top-level arrays natively. For `List<T>` return types, fall back to prompt-based approach.

## StructuredOutputValidationAdvisor (retry on parse failure)

Spring AI 1.1+ provides a recursive advisor that validates JSON output against the expected schema and retries with augmented error context:

```java
var validationAdvisor = StructuredOutputValidationAdvisor.builder()
    .outputType(MyResponseType.class)
    .maxRepeatAttempts(3)
    .build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(validationAdvisor)
    .build();

MyResponseType result = chatClient.prompt("Analyze this data...")
    .call()
    .entity(MyResponseType.class);
```

**Important considerations**:
- Each retry is an additional LLM API call — keep `maxRepeatAttempts` at 2–3
- Does not support streaming
- Add `SimpleLoggerAdvisor` during development to log raw JSON responses

## Model-specific JSON mode configuration

| Provider | Property | Values |
|----------|----------|--------|
| OpenAI | `spring.ai.openai.chat.options.responseFormat` | `JSON_OBJECT`, `JSON_SCHEMA` |
| Azure OpenAI | `spring.ai.azure.openai.chat.options.responseFormat` | `{"type": "json_object"}` |
| Ollama | `spring.ai.ollama.chat.options.format` | `json` |
| Mistral AI | `spring.ai.mistralai.chat.options.responseFormat` | `{"type": "json_object"}` or `{"type": "json_schema"}` |

For OpenAI strict mode, combine `BeanOutputConverter.getJsonSchema()` with `ResponseFormat.Type.JSON_SCHEMA` in `OpenAiChatOptions`.

## Best practices checklist

1. **Prefer `ChatClient.entity()` over raw ChatModel** — less boilerplate, automatic format injection
2. **Use Java records** for structured output types — immutable, concise, Jackson-friendly
3. **Annotate fields with `@JsonPropertyDescription`** — richer schema = better LLM accuracy
4. **Enable native structured output** when the target model supports it
5. **Add `StructuredOutputValidationAdvisor`** with max 3 retries for production resilience
6. **Use `.responseEntity()` instead of separate `.entity()` + `.chatResponse()`** to avoid double API calls
7. **Wrap collections in a record** when using native structured output to avoid top-level array issues:
   ```java
   // Instead of List<Movie>, use:
   record MovieList(List<Movie> movies) {}
   ```
8. **Never assume the LLM returns valid JSON** — always handle parse exceptions gracefully
9. **Log raw responses during development** with `SimpleLoggerAdvisor`
10. **Test with malformed inputs** to verify retry behavior under adverse conditions
