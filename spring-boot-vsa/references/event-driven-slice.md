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

Key detail: the event is published **inside** the transaction. By default Spring holds the event until the transaction commits, then delivers it — so listeners never see a state that rolled back. (Spring does this automatically when listeners are `@TransactionalEventListener`; with plain `@EventListener` the delivery is synchronous-to-publish, but `@Async` immediately hands off to another thread, so the downstream work still runs outside the publisher's transaction.)

If you need stricter "only fire if commit succeeded" guarantees, use `@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)` on the listener.

## Step 4 — listen in another slice

`features/notification/handlers/OrderCompletedNotificationListener.java`:

```java
package com.acme.ordering.features.notification.handlers;

import com.acme.ordering.features.notification.model.Notification;
import com.acme.ordering.features.notification.model.NotificationRepository;
import com.acme.ordering.features.order.events.OrderCompletedEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class OrderCompletedNotificationListener {

    private final NotificationRepository notificationRepository;

    @Async("taskExecutor")
    @EventListener
    @Transactional
    public void onOrderCompleted(OrderCompletedEvent event) {
        log.info("Sending notification for completed order id={}", event.orderId());

        Notification notification = Notification.builder()
                .customerId(event.customerId())
                .message("Your order #" + event.orderId() + " is complete.")
                .build();

        notificationRepository.save(notification);
    }
}
```

Important details:
- **`@Async("taskExecutor")`** — hands off to the thread pool; the publisher doesn't block.
- **`@Transactional`** is on the listener itself — it runs outside the publisher's transaction and owns its own unit of work.
- **One listener method per event reaction.** If the notification slice also cares about `OrderCancelledEvent`, that's a second method (or a second class).

**Cross-slice import note:** the listener imports `OrderCompletedEvent` from `features/order/events/`. This is the **only** kind of cross-slice import VSA allows — events are a published contract, not implementation details. Importing another slice's handler, entity, or repository is a violation; importing its event is fine.

## Common pitfalls

- **`@Async` silently ignored.** Happens when the annotation is on a method called from the same class, or when `@EnableAsync` is missing. Always put listeners in a `@Service` class and invoke them only via Spring events, never via direct method call.
- **Listener throws but publisher doesn't know.** That's by design — but it means you need monitoring on listeners. Log exceptions and consider a dead-letter mechanism for critical workflows.
- **Transaction boundary confusion.** If a listener is `@Transactional` and the publisher is also `@Transactional`, they are two separate transactions. A listener cannot roll back the publisher.
- **Event shape churning.** Once multiple listeners depend on an event, changing the record's components is a breaking change across slices. Version the event (e.g. `OrderCompletedEventV2`) rather than modifying the original.
