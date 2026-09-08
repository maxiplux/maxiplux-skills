# Worked example — event-driven slice

Use this pattern when a slice needs to trigger work in another slice without coupling them at compile time. The publishing handler emits a domain event via Spring's `ApplicationEventPublisher`; a listener in the same or a different slice reacts asynchronously.

**Scenario:** when an order is completed, a notification needs to be sent and an invoice generated. The `order` slice publishes `OrderCompletedEvent`. The `notification` and `invoice` slices each own a listener that reacts.

## Why events instead of direct calls?

Three reasons this is preferred over `orderHandler` directly calling `notificationHandler` and `invoiceHandler`:

1. **The `order` slice doesn't need to know `notification` or `invoice` exist.** It publishes a fact about its domain; downstream slices opt in.
2. **Adding a new consumer is zero-change to the publisher.** A new slice can subscribe without touching `order`.
3. **Listener work happens on a separate thread** via `@Async`, so slow email sending or PDF generation doesn't block the HTTP response.

The tradeoff: you lose the synchronous call stack. If the notification fails, the order is already saved. That's usually a feature, not a bug — retry the notification separately rather than rolling back the order — but be deliberate about choosing this pattern.

## Step 1 — configure the async executor (one-time, in shared/)

`shared/config/AsyncConfig.java`:

```java
package com.acme.ordering.shared.config;

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
        executor.initialize();
        return executor;
    }
}
```

The executor's name (`taskExecutor`) matters — listeners will reference it by that name.

If you scaffolded with `init_shared.py --with-json-logging`, `AsyncConfig` additionally wires `executor.setTaskDecorator(new MdcTaskDecorator());` so the caller's `requestId`/`traceId` MDC keys survive the hand-off to async threads. Without it, async log lines lose their correlation id.

## Step 2 — define the event in the publisher slice

`features/order/events/OrderCompletedEvent.java`:

```java
package com.acme.ordering.features.order.events;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Published when an Order transitions to COMPLETED.
 *
 * <p>Carries only the identifiers and minimal facts consumers need. Consumers
 * should re-read from their own slice's repository if they need more detail —
 * avoid bloating the event with every field of the entity.
 */
public record OrderCompletedEvent(
        Long orderId,
        Long customerId,
        BigDecimal total,
        Instant completedAt
) {
}
```

Two important guidelines for events:
- **Keep them small.** Include IDs + a few key facts. Not the whole entity.
- **Make them records.** Immutable, serializable, obvious.

## Step 3 — publish from the handler

`features/order/handlers/CompleteOrderHandler.java`:

```java
package com.acme.ordering.features.order.handlers;

import com.acme.ordering.features.order.events.OrderCompletedEvent;
import com.acme.ordering.features.order.exception.OrderNotFoundException;
import com.acme.ordering.features.order.model.Order;
import com.acme.ordering.features.order.model.OrderMapper;
import com.acme.ordering.features.order.model.OrderRepository;
import com.acme.ordering.features.order.enums.OrderStatus;
import com.acme.ordering.features.order.api.response.OrderResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;

@Service
@RequiredArgsConstructor
@Slf4j
public class CompleteOrderHandler {

    private final OrderRepository orderRepository;
    private final OrderMapper orderMapper;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional
    public OrderResponse handle(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));

        order.setStatus(OrderStatus.COMPLETED);
        order.setCompletedAt(Instant.now());

        log.info("Completed order id={} total={}", order.getId(), order.getTotal());

        eventPublisher.publishEvent(new OrderCompletedEvent(
                order.getId(),
                order.getCustomerId(),
                order.getTotal(),
                order.getCompletedAt()
        ));

        return orderMapper.toResponse(order);
    }
}
```

Key detail: the event is published **inside** the transaction, and delivery timing depends on the listener annotation:

- **Plain `@EventListener`** (used above) delivers **synchronously at publish time — before the transaction commits.** With `@Async` the listener body is immediately handed to another thread, so it runs outside (and unaware of) the publisher's transaction. If the publisher then rolls back, the listener has already fired: a notification may be sent for an order that never persisted.
- **`@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)`** holds the event until the transaction **commits**, then delivers it — so the listener never reacts to a state that rolled back.

Choose `@TransactionalEventListener(phase = AFTER_COMMIT)` when the reaction must only happen if the write succeeded (the common case for "send a notification / generate an invoice after X"). Use plain `@EventListener` only when firing on a not-yet-committed event is acceptable.

One footgun to know: `@TransactionalEventListener` **silently does nothing if the event is published outside a transaction** (its `fallbackExecution` defaults to `false`). That's fine here — `CompleteOrderHandler.handle` is `@Transactional` — but if you publish the same event from a non-transactional path, the listener won't fire. Set `fallbackExecution = true` if it must run either way.

## Step 4 — listen in another slice

`features/notification/handlers/OrderCompletedNotificationListener.java`:

```java
package com.acme.ordering.features.notification.handlers;

import com.acme.ordering.features.notification.model.Notification;
import com.acme.ordering.features.notification.model.NotificationRepository;
import com.acme.ordering.features.order.events.OrderCompletedEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Service
@RequiredArgsConstructor
@Slf4j
public class OrderCompletedNotificationListener {

    private final NotificationRepository notificationRepository;

    @Async("taskExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Transactional
    public void onOrderCompleted(OrderCompletedEvent event) {
        try {
            log.info("Sending notification for completed order id={}", event.orderId());

            Notification notification = Notification.builder()
                    .customerId(event.customerId())
                    .message("Your order #" + event.orderId() + " is complete.")
                    .build();

            notificationRepository.save(notification);
        } catch (Exception ex) {
            // Async path: no HTTP boundary will ever log this — the listener MUST log.error locally.
            log.error("Failed to create notification for completed order id={}", event.orderId(), ex);
        }
    }
}
```

Important details:
- **`@Async("taskExecutor")`** — hands off to the thread pool; the publisher doesn't block.
- **`@TransactionalEventListener(phase = AFTER_COMMIT)`** — the notification only fires once the order transaction has committed, so a rolled-back order never triggers a "your order is complete" message. (Plain `@EventListener` would fire before commit — see the delivery-timing note above.)
- **`@Transactional`** is on the listener itself — after commit it starts its own new unit of work to persist the notification.
- **The try/catch with local `log.error(..., ex)` is mandatory.** An uncaught exception on an async thread never reaches `GlobalExceptionHandler` — it disappears into the executor.
- **One listener method per event reaction.** If the notification slice also cares about `OrderCancelledEvent`, that's a second method (or a second class).

**Cross-slice import note:** the listener imports `OrderCompletedEvent` from `features/order/events/`. This is the **only** kind of cross-slice import VSA allows — events are a published contract, not implementation details. Importing another slice's handler, entity, or repository is a violation; importing its event is fine.

## Common pitfalls

- **`@Async` silently ignored.** Happens when the annotation is on a method called from the same class, or when `@EnableAsync` is missing. Always put listeners in a `@Service` class and invoke them only via Spring events, never via direct method call.
- **Listener throws but publisher doesn't know.** That's by design — and it's exactly why every async listener catches and `log.error`s locally, with the throwable as the last argument. An uncaught listener exception disappears into the executor. Consider a dead-letter mechanism for critical workflows.
- **Transaction boundary confusion.** If a listener is `@Transactional` and the publisher is also `@Transactional`, they are two separate transactions. A listener cannot roll back the publisher.
- **Event shape churning.** Once multiple listeners depend on an event, changing the record's components is a breaking change across slices. Version the event (e.g. `OrderCompletedEventV2`) rather than modifying the original.
