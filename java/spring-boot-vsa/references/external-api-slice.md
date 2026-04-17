# Worked example — slice with an external API call

Use this pattern when a slice depends on a third-party service (payment gateway, email provider, geocoding API, AI model, etc.). The slice owns its own client, wraps calls with `@Retryable`, falls back gracefully on persistent failure, and tracks the outcome.

**Scenario:** a `geocoding` slice resolves a street address to latitude/longitude by calling an external geocoding API. Transient failures retry automatically; permanent failures return a typed "unresolvable" result without crashing the caller.

## Where the client lives

When only one slice calls the external service, the client class lives **inside that slice** — not in `shared/`. Only when a second slice genuinely needs the same client does it move to `shared/`.

Layout for our example:

```
com/acme/places/features/geocoding/
├── api/
│   ├── GeocodingController.java
│   ├── request/GeocodeAddressRequest.java
│   └── response/GeocodeResponse.java
├── client/
│   └── ExternalGeocoderClient.java      <- lives inside the slice
├── exception/
│   └── GeocodingUnavailableException.java
└── handlers/
    └── GeocodeAddressHandler.java
```

The `client/` subfolder is a sensible extension to the standard slice layout for this pattern. Other options: put it in `handlers/` (it's arguably business-logic infrastructure) or `model/` (less conventional). Pick one and be consistent within the project.

## Step 1 — one-time retry configuration

Add `@EnableRetry` to the main application class:

```java
@SpringBootApplication
@EnableRetry
@EnableAsync
public class PlacesApplication {
    public static void main(String[] args) { SpringApplication.run(PlacesApplication.class, args); }
}
```

Depends on `org.springframework.retry:spring-retry` and `org.springframework:spring-aspects`.

## Step 2 — the client with `@Retryable` + `@Recover`

```java
package com.acme.places.features.geocoding.client;

import com.acme.places.features.geocoding.exception.GeocodingUnavailableException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component
@RequiredArgsConstructor
@Slf4j
public class ExternalGeocoderClient {

    private final RestClient restClient;

    @Value("${app.geocoding.api-key}")
    private String apiKey;

    @Retryable(
            retryFor = RestClientException.class,
            maxAttempts = 3,
            backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public GeocodeResult geocode(String address) {
        log.debug("Geocoding address='{}'", address);
        ExternalResponse response = restClient.get()
                .uri(uri -> uri.path("/v1/geocode")
                        .queryParam("address", address)
                        .queryParam("key", apiKey)
                        .build())
                .retrieve()
                .body(ExternalResponse.class);

        if (response == null || response.latitude() == null) {
            throw new RestClientException("Empty response from geocoder");
        }
        return new GeocodeResult(response.latitude(), response.longitude(), false);
    }

    @Recover
    public GeocodeResult recover(RestClientException ex, String address) {
        log.warn("Geocoder unavailable after retries for address='{}': {}", address, ex.getMessage());
        throw new GeocodingUnavailableException(address, ex);
    }

    public record GeocodeResult(Double latitude, Double longitude, boolean fallback) {}
    private record ExternalResponse(Double latitude, Double longitude) {}
}
```

Three things to notice:

1. **`@Retryable(retryFor = RestClientException.class, ...)`** — only retry on the exception classes that indicate a transient failure. Don't retry on `4xx` responses caused by bad input; those will never succeed.
2. **`@Recover` method signature matches the retried method + the exception as the first param.** Spring picks this method when retries exhaust. The `@Recover` method must return the same type as the retryable method (or a subtype).
3. **The `@Recover` here escalates** by throwing a typed domain exception — callers can catch it specifically rather than squinting at `RestClientException`. An alternative is to return a fallback `GeocodeResult` with `fallback = true`; pick whichever makes sense for your caller.

## Step 3 — slice-specific exception

```java
package com.acme.places.features.geocoding.exception;

public class GeocodingUnavailableException extends RuntimeException {
    public GeocodingUnavailableException(String address, Throwable cause) {
        super("Geocoding service unavailable for address: " + address, cause);
    }
}
```

Mapped to HTTP 503 in `GlobalExceptionHandler`:

```java
@ExceptionHandler(GeocodingUnavailableException.class)
public ProblemDetail handleGeocodingUnavailable(GeocodingUnavailableException ex) {
    ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.SERVICE_UNAVAILABLE, ex.getMessage());
    problem.setType(URI.create("https://api.example.com/problems/upstream-unavailable"));
    return problem;
}
```

## Step 4 — the handler uses the client

```java
package com.acme.places.features.geocoding.handlers;

import com.acme.places.features.geocoding.api.request.GeocodeAddressRequest;
import com.acme.places.features.geocoding.api.response.GeocodeResponse;
import com.acme.places.features.geocoding.client.ExternalGeocoderClient;
import com.acme.places.features.geocoding.client.ExternalGeocoderClient.GeocodeResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class GeocodeAddressHandler {

    private final ExternalGeocoderClient geocoderClient;

    @Transactional(readOnly = true)
    public GeocodeResponse handle(GeocodeAddressRequest request) {
        GeocodeResult result = geocoderClient.geocode(request.address());
        log.info("Geocoded address='{}' -> lat={} lon={}",
                 request.address(), result.latitude(), result.longitude());
        return new GeocodeResponse(result.latitude(), result.longitude(), result.fallback());
    }
}
```

The handler is trivial — it delegates to the client and maps to the response record. Retry logic, fallbacks, and recovery are all inside the client where they belong.

## Multi-provider fallback (primary + fallback + basic)

For higher-value external calls (e.g. AI model, payment gateway), a three-tier fallback is common:

```java
public EvaluationResult evaluate(String input) {
    try {
        return primaryProvider.evaluate(input);   // e.g. Gemini
    } catch (Exception primaryEx) {
        log.warn("Primary provider failed, trying fallback: {}", primaryEx.getMessage());
        try {
            return fallbackProvider.evaluate(input); // e.g. Claude
        } catch (Exception fallbackEx) {
            log.warn("Fallback provider failed, using basic: {}", fallbackEx.getMessage());
            return basicHeuristic(input);           // deterministic, always works
        }
    }
}
```

Each provider call can still be wrapped with its own `@Retryable` — put the retry on the inner method that actually makes the HTTP call, and the tiered fallback on the outer orchestrating method.

## Common pitfalls

- **`@Retryable` silently ignored.** Happens when the annotated method is called from within the same class (self-invocation bypasses the proxy). Always inject the bean and call through the Spring-managed reference.
- **`@Recover` method signature mismatch.** If the return type or parameter types don't align with the `@Retryable` method, Spring doesn't find it and you get the underlying exception instead of the recovery value. The first parameter must be the exception type.
- **Retrying on non-transient failures.** A 400 Bad Request will still be 400 on the third try. Use `retryFor` / `noRetryFor` to scope retries.
- **Leaking the external API's types across the boundary.** Keep the external response DTO private to the client; translate to a slice-owned record before returning.
- **Timeouts not configured.** A hanging request that never fails defeats the retry mechanism. Configure connect/read timeouts on the `RestClient` / `WebClient`.
