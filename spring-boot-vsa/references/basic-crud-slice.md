# Worked example — basic CRUD slice

This is what a complete, filled-in CRUD slice looks like after the scaffolding script has been run and the TODO comments have been replaced with real domain logic. Use this as a reference when expanding the scaffolded skeleton.

**Feature:** `payment` — a simple "record a payment" domain with status tracking.
**Base package:** `com.acme.billing`

## Directory layout

```
com/acme/billing/features/payment/
├── api/
│   ├── PaymentController.java
│   ├── request/
│   │   ├── CreatePaymentRequest.java
│   │   └── UpdatePaymentRequest.java
│   └── response/
│       └── PaymentResponse.java
├── enums/
│   └── PaymentStatus.java
├── exception/
│   └── PaymentNotFoundException.java
├── handlers/
│   ├── CreatePaymentHandler.java
│   ├── ListPaymentHandler.java
│   ├── GetPaymentHandler.java
│   ├── UpdatePaymentHandler.java
│   └── DeletePaymentHandler.java
└── model/
    ├── Payment.java
    ├── PaymentMapper.java
    └── PaymentRepository.java
```

## What this slice relies on in shared/

Scaffolded once per project with `python scripts/init_shared.py --base-package com.acme.billing`:

```
com/acme/billing/shared/
├── config/AsyncConfig.java
├── entity/BaseEntity.java                  <- Payment extends this
├── exception/EntityNotFoundException.java  <- PaymentNotFoundException extends this
└── exception/GlobalExceptionHandler.java   <- maps exceptions to RFC 9457 ProblemDetail
```

## Entity — real domain fields

```java
package com.acme.billing.features.payment.model;

import com.acme.billing.features.payment.enums.PaymentStatus;
import com.acme.billing.shared.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "payments")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Payment extends BaseEntity {

    @Column(nullable = false, length = 64)
    private String reference;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal amount;

    @Column(nullable = false, length = 3)
    private String currency;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private PaymentStatus status;

    private Instant processedAt;
}
```

Key things to notice:
- `BigDecimal` for money, never `double` or `float`
- `@Enumerated(EnumType.STRING)` — never ordinal
- Extends `BaseEntity` for `id`, `createdAt`, `updatedAt` audit fields
- Explicit `@Column(nullable = false)` where appropriate — don't rely on DB defaults

## Slice-specific enum

```java
package com.acme.billing.features.payment.enums;

public enum PaymentStatus {
    PENDING,
    PROCESSING,
    COMPLETED,
    FAILED,
    REFUNDED
}
```

Enums live in `{slice}/enums/` — never in a shared `enums/` package unless they're genuinely used by 2+ slices.

## Repository — bounded queries

```java
package com.acme.billing.features.payment.model;

import com.acme.billing.features.payment.enums.PaymentStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Long> {

    Optional<Payment> findByReference(String reference);

    Page<Payment> findByStatus(PaymentStatus status, Pageable pageable);
}
```

Both query methods are bounded — the `Page<Payment>` method forces the caller to paginate, and `findByReference` returns at most one row (constrained by a unique reference).

## Response record

```java
package com.acme.billing.features.payment.api.response;

import com.acme.billing.features.payment.enums.PaymentStatus;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.Instant;

@Schema(description = "Representation of a Payment returned by the API")
public record PaymentResponse(

        @Schema(description = "Unique identifier", example = "42")
        Long id,

        @Schema(description = "Unique payment reference", example = "INV-2026-0042")
        String reference,

        @Schema(description = "Payment amount in the given currency", example = "199.99")
        BigDecimal amount,

        @Schema(description = "ISO 4217 currency code", example = "EUR")
        String currency,

        @Schema(description = "Current payment status", example = "PENDING")
        PaymentStatus status,

        @Schema(description = "When the payment was processed (UTC)", example = "2026-07-17T09:30:00Z")
        Instant processedAt,

        @Schema(description = "Creation timestamp (UTC)", example = "2026-07-17T09:29:12Z")
        Instant createdAt,

        @Schema(description = "Last-update timestamp (UTC)", example = "2026-07-17T09:30:00Z")
        Instant updatedAt
) {
}
```

The response exposes the enum directly — Spring serializes it as a string because it's `EnumType.STRING`. Every field carries `@Schema(description, example)` — springdoc composes the field examples into a complete example response body in the API docs.

## Request records — validation at the boundary

```java
package com.acme.billing.features.payment.api.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record CreatePaymentRequest(

        @NotBlank
        @Size(max = 64)
        @Schema(description = "Unique payment reference", example = "INV-2026-0042",
                requiredMode = Schema.RequiredMode.REQUIRED)
        String reference,

        @NotNull
        @DecimalMin("0.01")
        @Schema(description = "Payment amount in the given currency", example = "199.99",
                requiredMode = Schema.RequiredMode.REQUIRED)
        BigDecimal amount,

        @NotBlank
        @Size(min = 3, max = 3)
        @Schema(description = "ISO 4217 currency code", example = "EUR",
                requiredMode = Schema.RequiredMode.REQUIRED)
        String currency
) {
}
```

Validation annotations on record components are picked up by `@Valid` on the controller parameter. The handler never re-validates — if the request got to the handler, it's valid. Every field also carries `@Schema(description, example, requiredMode)` — request examples are the first of the three mandatory example parts (request, response, error).

## Controller — request, response, and error examples

The scaffolded controller documents all three example parts: **request examples** come from the request DTO's `@Schema(example = ...)` fields, **response examples** from the response DTO's fields plus the success `content` schema, and **error examples** from `@ExampleObject` ProblemDetail bodies. This is the GET endpoint exactly as `create_slice.py` generates it:

```java
@GetMapping("/{id}")
@Operation(summary = "Get a payment by id",
        description = "Returns the payment with the given id, or an RFC 9457 problem response if it does not exist.")
@ApiResponses({
        @ApiResponse(responseCode = "200", description = "Found",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = PaymentResponse.class))),
        @ApiResponse(responseCode = "404", description = "Payment not found",
                content = @Content(mediaType = "application/problem+json",
                        schema = @Schema(implementation = ProblemDetail.class),
                        examples = @ExampleObject(name = "not-found", value = """
                                {
                                  "type": "https://api.example.com/problems/not-found",
                                  "title": "Resource not found",
                                  "status": 404,
                                  "detail": "Payment not found: id=42",
                                  "instance": "/api/v1/payments/42"
                                }
                                """))),
})
public PaymentResponse get(@PathVariable Long id) {
    return getPaymentHandler.handle(id);
}
```

Every error status an endpoint can return gets the same treatment — `application/problem+json` content, `ProblemDetail` schema, and a realistic `@ExampleObject`.

## Handler — create

```java
package com.acme.billing.features.payment.handlers;

import com.acme.billing.features.payment.api.request.CreatePaymentRequest;
import com.acme.billing.features.payment.api.response.PaymentResponse;
import com.acme.billing.features.payment.enums.PaymentStatus;
import com.acme.billing.features.payment.model.Payment;
import com.acme.billing.features.payment.model.PaymentMapper;
import com.acme.billing.features.payment.model.PaymentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class CreatePaymentHandler {

    private final PaymentRepository paymentRepository;
    private final PaymentMapper paymentMapper;

    @Transactional
    public PaymentResponse handle(CreatePaymentRequest request) {
        Payment entity = paymentMapper.toEntity(request);
        entity.setStatus(PaymentStatus.PENDING);
        Payment saved = paymentRepository.save(entity);
        log.info("Created payment id={} reference={}", saved.getId(), saved.getReference());
        return paymentMapper.toResponse(saved);
    }
}
```

Handler responsibilities:
1. Convert request record to entity via the mapper
2. Apply any defaults the request doesn't carry (here: `status = PENDING`)
3. Persist
4. Log at the transaction boundary
5. Convert back to a response record

Notice what's **not** here: no validation (already done), no try/catch (exceptions bubble to `GlobalExceptionHandler`), no HTTP concerns (those belong in the controller).

## Mapper

```java
package com.acme.billing.features.payment.model;

import com.acme.billing.features.payment.api.request.CreatePaymentRequest;
import com.acme.billing.features.payment.api.request.UpdatePaymentRequest;
import com.acme.billing.features.payment.api.response.PaymentResponse;
import org.springframework.stereotype.Component;

@Component
public class PaymentMapper {

    public Payment toEntity(CreatePaymentRequest request) {
        return Payment.builder()
                .reference(request.reference())
                .amount(request.amount())
                .currency(request.currency().toUpperCase())
                .build();
    }

    public void applyUpdate(Payment entity, UpdatePaymentRequest request) {
        entity.setReference(request.reference());
        entity.setAmount(request.amount());
        entity.setCurrency(request.currency().toUpperCase());
    }

    public PaymentResponse toResponse(Payment entity) {
        return new PaymentResponse(
                entity.getId(),
                entity.getReference(),
                entity.getAmount(),
                entity.getCurrency(),
                entity.getStatus(),
                entity.getProcessedAt(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }
}
```

The `applyUpdate` method mutates a managed entity — no explicit `save` call needed because JPA dirty-checking handles it while the transaction is open.

## Global exception handler (in shared/)

`PaymentNotFoundException` extends the shared `EntityNotFoundException` base, so the one handler below maps every not-found exception across every slice — no per-slice `@ExceptionHandler` is ever written. This is `shared/exception/GlobalExceptionHandler.java` exactly as `init_shared.py` scaffolds it:

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

/**
 * Single HTTP error boundary for the whole application (RFC 9457 Problem Details).
 *
 * <p>Framework exceptions (validation, type mismatch, unknown route, ...) are handled by
 * {@link ResponseEntityExceptionHandler}; set {@code spring.mvc.problemdetails.enabled=true}
 * so they render as {@code application/problem+json}. Only domain exceptions and the
 * catch-all live here.
 *
 * <p><strong>Logging contract:</strong> this class is the ONLY place that logs HTTP request
 * failures. Handlers that throw must not also {@code log.error} the same failure.
 */
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

Framework exceptions (validation, type mismatch, unknown route) become ProblemDetail automatically through the inherited `ResponseEntityExceptionHandler` — just set `spring.mvc.problemdetails.enabled=true` in `application.yml`/`.properties`. One handler, every "not found" across every slice.
