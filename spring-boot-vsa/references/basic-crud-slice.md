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
        Long id,
        String reference,
        BigDecimal amount,
        String currency,
        PaymentStatus status,
        Instant processedAt,
        Instant createdAt,
        Instant updatedAt
) {
}
```

The response exposes the enum directly — Spring serializes it as a string because it's `EnumType.STRING`.

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
        @NotBlank @Size(max = 64) String reference,
        @NotNull @DecimalMin("0.01") BigDecimal amount,
        @NotBlank @Size(min = 3, max = 3) String currency
) {
}
```

Validation annotations on record components are picked up by `@Valid` on the controller parameter. The handler never re-validates — if the request got to the handler, it's valid.

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

## Global exception handler mapping (in shared/)

The `PaymentNotFoundException` extends `RuntimeException` (or a shared `EntityNotFoundException` base). In `shared/exception/GlobalExceptionHandler.java` you'd have something like:

```java
@ExceptionHandler(PaymentNotFoundException.class)
public ProblemDetail handleNotFound(PaymentNotFoundException ex) {
    ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    problem.setType(URI.create("https://api.example.com/problems/not-found"));
    return problem;
}
```

Or, if you use a common base (preferred):

```java
@ExceptionHandler(EntityNotFoundException.class)
public ProblemDetail handleNotFound(EntityNotFoundException ex) { ... }
```

One handler, every "not found" exception across every slice.
