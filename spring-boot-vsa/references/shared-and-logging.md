# Worked example — shared/ package and structured logging

Everything `scripts/init_shared.py` scaffolds, rendered for base package `com.acme.billing`, plus the Boot 2.x fallback and the JSON/MDC logging setup. Run the script once per project, **before** the first slice:

```bash
python scripts/init_shared.py --base-package com.acme.billing --output-dir src/main/java
# add --with-json-logging for JSON logs + MDC request correlation
```

## Generated tree

```
src/main/java/com/acme/billing/shared/
├── config/
│   ├── AsyncConfig.java            # always
│   ├── RequestIdFilter.java        # only with --with-json-logging
│   └── MdcTaskDecorator.java       # only with --with-json-logging
├── entity/
│   └── BaseEntity.java             # always
└── exception/
    ├── EntityNotFoundException.java    # always
    └── GlobalExceptionHandler.java     # always
src/main/resources/
└── logback-spring.xml              # only with --with-json-logging
```

The script never overwrites existing files — re-running is always safe.

## BaseEntity

```java
package com.acme.billing.shared.entity;

import jakarta.persistence.Column;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.Instant;

@MappedSuperclass
@Getter
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(nullable = false)
    private Instant updatedAt;
}
```

Every slice entity extends this — the slice `Mapper` reads `getId()`, `getCreatedAt()`, `getUpdatedAt()` from it. Hibernate's timestamp annotations need no `@EnableJpaAuditing`; if the project uses Spring Data auditing instead, swap in `@CreatedDate`/`@LastModifiedDate` + `@EntityListeners(AuditingEntityListener.class)`.

## EntityNotFoundException

```java
package com.acme.billing.shared.exception;

public abstract class EntityNotFoundException extends RuntimeException {

    protected EntityNotFoundException(String message) {
        super(message);
    }
}
```

Every slice's `{Feature}NotFoundException` extends this, so one `@ExceptionHandler` maps all of them to 404. Abstract on purpose — always throw the typed slice exception. **Naming caution:** distinct from `jakarta.persistence.EntityNotFoundException` (same simple name) — never import the jakarta one in shared code; JPA's own exception intentionally falls through to the 500 catch-all.

## GlobalExceptionHandler

```java
package com.acme.billing.shared.exception;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.net.URI;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    private static final String PROBLEM_BASE = "https://api.example.com/problems/";

    @ExceptionHandler(EntityNotFoundException.class)
    public ProblemDetail handleNotFound(EntityNotFoundException ex, HttpServletRequest request) {
        // Domain 4xx: expected failure — ERROR without the throwable (no stack-trace noise).
        log.error("Resource not found: {} [{} {}]", ex.getMessage(), request.getMethod(), request.getRequestURI());
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource not found");
        problem.setType(URI.create(PROBLEM_BASE + "not-found"));
        problem.setInstance(URI.create(request.getRequestURI()));
        return problem;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex, HttpServletRequest request) {
        // Unexpected 5xx: full stack trace — throwable as the LAST argument.
        log.error("Unhandled exception on {} {}", request.getMethod(), request.getRequestURI(), ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
        problem.setTitle("Internal server error");
        problem.setType(URI.create(PROBLEM_BASE + "internal-error"));
        problem.setInstance(URI.create(request.getRequestURI()));
        return problem;
    }
}
```

Replace `PROBLEM_BASE` with your API's real problem-type URI prefix. Domain exceptions that need their own status (e.g. upstream unavailable → 503) get **additional `@ExceptionHandler` methods on this same class** — never a second `@RestControllerAdvice`.

### spring.mvc.problemdetails.enabled

```yaml
spring:
  mvc:
    problemdetails:
      enabled: true
```

With this flag on, the inherited `ResponseEntityExceptionHandler` converts framework exceptions (`MethodArgumentNotValidException`, `HttpMessageNotReadableException`, type mismatches, unknown routes, ...) to `application/problem+json` automatically — no hand-written validation handler. A failed `@Valid` request renders like:

```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid request content.",
  "instance": "/api/v1/payments"
}
```

## Logging decision table

| Situation | Level | Throwable as last arg? | Who logs it |
|---|---|---|---|
| Domain 4xx (not-found, business rule) | `error` | No — expected failure, no stack trace | `GlobalExceptionHandler` only |
| Unexpected 5xx | `error` | Yes | `GlobalExceptionHandler` only |
| Async listener failure (swallowed) | `error` | Yes | The listener itself (try/catch) — nothing else ever sees it |
| `@Recover` that swallows (returns a fallback) | `error` | Yes | The `@Recover` method |
| `@Recover` that rethrows a mapped domain exception | — | — | The boundary logs it; don't log in `@Recover` (double-log) |
| Scheduled job failure (swallowed) | `error` | Yes | The job itself (try/catch) |
| Happy path | `info`/`debug` | — | The handler, ids only — never full DTOs |

A handler that throws must **not** also `log.error` the failure — `GlobalExceptionHandler` is the single HTTP boundary. Async/`@Recover`/scheduled paths have no HTTP boundary, which is why they log locally.

## Boot 2.x fallback (no ProblemDetail)

`org.springframework.http.ProblemDetail` is a Spring Framework 6 / Boot 3 type. On Boot 2.x, hand-roll the same RFC 9457 shape (records need Java 16+; Boot 2.7 on Java 17 works — on older Java use a small class):

```java
/** RFC 9457-shaped error body for Spring Boot 2.x, which has no ProblemDetail. */
public record ErrorResponse(String type, String title, int status, String detail, String instance) {}
```

```java
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final MediaType PROBLEM_JSON = MediaType.parseMediaType("application/problem+json");

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(EntityNotFoundException ex, HttpServletRequest request) {
        log.error("Resource not found: {} [{} {}]", ex.getMessage(), request.getMethod(), request.getRequestURI());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).contentType(PROBLEM_JSON)
                .body(new ErrorResponse("https://api.example.com/problems/not-found",
                        "Resource not found", 404, ex.getMessage(), request.getRequestURI()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception ex, HttpServletRequest request) {
        log.error("Unhandled exception on {} {}", request.getMethod(), request.getRequestURI(), ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).contentType(PROBLEM_JSON)
                .body(new ErrorResponse("https://api.example.com/problems/internal-error",
                        "Internal server error", 500, "An unexpected error occurred", request.getRequestURI()));
    }
}
```

Same logging contract, same media type, same field names — only the carrier type differs.

## JSON logging + MDC correlation (opt-in)

Scaffolded by `init_shared.py --with-json-logging`. Three pieces:

### 1. AsyncConfig (MDC variant)

```java
package com.acme.billing.shared.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("app-async-");
        executor.setTaskDecorator(new MdcTaskDecorator());
        executor.initialize();
        return executor;
    }
}
```

Without `--with-json-logging` the `setTaskDecorator` line is omitted; everything else is identical.

### 2. RequestIdFilter

```java
package com.acme.billing.shared.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

    public static final String HEADER = "X-Request-Id";
    public static final String MDC_REQUEST_ID = "requestId";
    public static final String MDC_TRACE_ID = "traceId";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String requestId = request.getHeader(HEADER);
        if (requestId == null || requestId.isBlank()) {
            requestId = UUID.randomUUID().toString();
        }
        MDC.put(MDC_REQUEST_ID, requestId);
        MDC.put(MDC_TRACE_ID, requestId);
        response.setHeader(HEADER, requestId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.clear();
        }
    }
}
```

A plain `@Component` — Spring Boot auto-registers every `Filter` bean, no `FilterRegistrationBean` needed. `@Order(Ordered.HIGHEST_PRECEDENCE)` runs it before everything else so even early failures carry the id; `MDC.clear()` in `finally` stops leakage across pooled server threads.

### 3. MdcTaskDecorator

```java
package com.acme.billing.shared.config;

import org.slf4j.MDC;
import org.springframework.core.task.TaskDecorator;

import java.util.Map;

public class MdcTaskDecorator implements TaskDecorator {

    @Override
    public Runnable decorate(Runnable runnable) {
        Map<String, String> contextMap = MDC.getCopyOfContextMap();
        return () -> {
            if (contextMap != null) {
                MDC.setContextMap(contextMap);
            }
            try {
                runnable.run();
            } finally {
                MDC.clear();
            }
        };
    }
}
```

MDC is thread-local — without this decorator, `@Async` listener log lines lose their `requestId`.

### Dependency

```xml
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>8.1</version> <!-- check for the latest version -->
</dependency>
```

```groovy
implementation 'net.logstash.logback:logstash-logback-encoder:8.1'          // Gradle
implementation("net.logstash.logback:logstash-logback-encoder:8.1")         // Kotlin DSL
```

### Activation and verification

The scaffolded `logback-spring.xml` is profile-gated: without the `json-logging` profile you get a human-readable pattern (which still shows `[requestId]`), with it you get one JSON object per line.

```bash
SPRING_PROFILES_ACTIVE=json-logging ./gradlew bootRun     # or --spring.profiles.active=json-logging
```

Verify correlation end-to-end:

```bash
curl -s -D - http://localhost:8080/api/v1/payments/42 -o /dev/null | grep X-Request-Id
```

The response echoes `X-Request-Id`, and every log line for that request carries the same id — `LogstashEncoder` emits the full MDC by default:

```json
{"@timestamp":"2026-07-17T09:30:00.123+00:00","message":"Resource not found: Payment not found: id=42 [GET /api/v1/payments/42]","logger_name":"com.acme.billing.shared.exception.GlobalExceptionHandler","thread_name":"http-nio-8080-exec-1","level":"ERROR","requestId":"7f3d2a1e-...","traceId":"7f3d2a1e-...","app":"billing"}
```
