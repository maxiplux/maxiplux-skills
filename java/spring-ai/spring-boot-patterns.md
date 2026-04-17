# Spring Boot Patterns & Best Practices Reference

## Architecture: Vertical Slices Architecture (VSA)

Organize code by feature, not by layer. Each feature is self-contained under `features/`:

```
app.quantun/
└── features/
    ├── procurement/
    │   ├── create-order/
    │   │   ├── api/
    │   │   │   ├── request/
    │   │   │   │   └── CreateOrderRequest.java
    │   │   │   └── response/
    │   │   │       └── CreateOrderResponse.java
    │   │   ├── handlers/
    │   │   │   └── CreateOrderHandler.java
    │   │   ├── model/
    │   │   │   └── Order.java
    │   │   ├── enums/
    │   │   │   └── OrderStatus.java
    │   │   └── exception/
    │   │       └── OrderNotFoundException.java
    │   └── approve-order/
    │       └── ...
    └── auth/
        ├── login/
        └── register/
```

**One handler per use case.** Each handler owns its request/response types, validation, and business logic. Shared domain models live in a `shared/` or `common/` directory.

## Project structure conventions

```
src/main/java/com/example/app/
├── config/           # Spring configuration beans
├── shared/           # Cross-cutting concerns
│   ├── exception/    # Global exception handlers
│   ├── security/     # Security filters, JWT utils
│   ├── logging/      # Logging interceptors
│   └── model/        # Shared domain entities
├── features/         # VSA feature slices
└── Application.java

src/main/resources/
├── application.properties     # Non-secret config only
├── db/migration/              # Flyway migrations
├── prompts/                   # Spring AI prompt templates
│   ├── system/
│   └── user/
└── static/                    # Static assets if needed
```

## REST API design

### Controller pattern

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
@Slf4j
public class OrderController {

    private final CreateOrderHandler createOrderHandler;
    private final GetOrderHandler getOrderHandler;

    @PostMapping
    public ResponseEntity<CreateOrderResponse> createOrder(
            @Valid @RequestBody CreateOrderRequest request) {
        log.info("Creating order, customerId={}", request.customerId());
        CreateOrderResponse response = createOrderHandler.handle(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> getOrder(@PathVariable UUID id) {
        return ResponseEntity.ok(getOrderHandler.handle(id));
    }
}
```

### Request/Response records

Always use Java records for DTOs. Use Jakarta validation annotations:

```java
public record CreateOrderRequest(
    @NotNull UUID customerId,
    @NotEmpty List<@Valid OrderItemRequest> items,
    @Size(max = 500) String notes
) {}

public record OrderItemRequest(
    @NotNull UUID productId,
    @Positive int quantity
) {}

public record CreateOrderResponse(
    UUID orderId,
    OrderStatus status,
    Instant createdAt
) {}
```

### Handler pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class CreateOrderHandler {

    private final OrderRepository orderRepository;
    private final InventoryService inventoryService;

    @Transactional
    public CreateOrderResponse handle(CreateOrderRequest request) {
        log.debug("Processing order, itemCount={}", request.items().size());

        inventoryService.validateAvailability(request.items());

        Order order = Order.builder()
            .customerId(request.customerId())
            .status(OrderStatus.PENDING)
            .items(mapItems(request.items()))
            .build();

        Order saved = orderRepository.save(order);
        log.info("Order created, orderId={}, status={}", saved.getId(), saved.getStatus());

        return new CreateOrderResponse(saved.getId(), saved.getStatus(), saved.getCreatedAt());
    }
}
```

## Exception handling

### Custom exception hierarchy

```java
public abstract class ApplicationException extends RuntimeException {
    private final String errorCode;
    private final HttpStatus httpStatus;

    protected ApplicationException(String message, String errorCode, HttpStatus httpStatus) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public String getErrorCode() { return errorCode; }
    public HttpStatus getHttpStatus() { return httpStatus; }
}

public class ResourceNotFoundException extends ApplicationException {
    public ResourceNotFoundException(String resource, Object id) {
        super("%s not found with id: %s".formatted(resource, id),
              "RESOURCE_NOT_FOUND", HttpStatus.NOT_FOUND);
    }
}

public class BusinessRuleViolationException extends ApplicationException {
    public BusinessRuleViolationException(String message) {
        super(message, "BUSINESS_RULE_VIOLATION", HttpStatus.UNPROCESSABLE_ENTITY);
    }
}
```

### Global exception handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    public record ErrorResponse(String errorCode, String message, Instant timestamp) {}

    @ExceptionHandler(ApplicationException.class)
    public ResponseEntity<ErrorResponse> handleApplicationException(ApplicationException ex) {
        log.warn("Application error, code={}, message={}", ex.getErrorCode(), ex.getMessage());
        return ResponseEntity.status(ex.getHttpStatus())
            .body(new ErrorResponse(ex.getErrorCode(), ex.getMessage(), Instant.now()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        String errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> "%s: %s".formatted(e.getField(), e.getDefaultMessage()))
            .collect(Collectors.joining(", "));
        log.warn("Validation failed, errors={}", errors);
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_FAILED", errors, Instant.now()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception ex) {
        log.error("Unexpected error", ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred", Instant.now()));
    }
}
```

## Spring Security

### JWT-based configuration (Spring Security 6+)

```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

### MFA with TOTP (preferred over OTT)

Use `dev.samstevens.totp` library for TOTP-based MFA:

```java
@Service
@RequiredArgsConstructor
public class TotpService {

    private final SecretGenerator secretGenerator = new DefaultSecretGenerator();

    public String generateSecret() {
        return secretGenerator.generate();
    }

    public boolean verifyCode(String secret, String code) {
        TimeProvider timeProvider = new SystemTimeProvider();
        CodeGenerator codeGenerator = new DefaultCodeGenerator();
        CodeVerifier verifier = new DefaultCodeVerifier(codeGenerator, timeProvider);
        return verifier.isValidCode(secret, code);
    }
}
```

### Cloudflare Turnstile integration

Validate turnstile tokens server-side before processing auth requests:

```java
@Service
@Slf4j
public class TurnstileService {

    private final RestClient restClient;
    private final String secretKey;

    public boolean verify(String token, String remoteIp) {
        TurnstileResponse response = restClient.post()
            .uri("https://challenges.cloudflare.com/turnstile/v0/siteverify")
            .body(Map.of("secret", secretKey, "response", token, "remoteip", remoteIp))
            .retrieve()
            .body(TurnstileResponse.class);

        if (!response.success()) {
            log.warn("Turnstile verification failed, errors={}", response.errorCodes());
        }
        return response.success();
    }

    record TurnstileResponse(boolean success,
                             @JsonProperty("error-codes") List<String> errorCodes) {}
}
```

## Logging standards

Use `@Slf4j` with structured key-value pairs. Apply tiered log levels:

| Level | Usage |
|-------|-------|
| `ERROR` | Failures requiring immediate attention (unhandled exceptions, data corruption) |
| `WARN` | Degraded state but recoverable (retry exhausted, fallback activated, validation failures) |
| `INFO` | Business events (order created, user registered, payment processed) |
| `DEBUG` | Internal details for troubleshooting (query params, intermediate calculations) |

```java
// Good — structured, contextual
log.info("Order created, orderId={}, customerId={}, total={}", orderId, customerId, total);
log.warn("Rate limit exceeded, clientId={}, endpoint={}", clientId, endpoint);
log.error("Payment processing failed, orderId={}, provider={}", orderId, provider, exception);

// Bad — unstructured, no context
log.info("Order created");
log.info("Order: " + order.toString());
```

## Database and Flyway

### Flyway migration naming

```
db/migration/
├── V1__create_users_table.sql
├── V2__create_orders_table.sql
├── V3__add_order_status_column.sql
└── V4__create_audit_log_table.sql
```

Always use `V{version}__{description}.sql` format. Never modify a committed migration.

### JPA entity patterns

```java
@Entity
@Table(name = "orders")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private UUID customerId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<OrderItem> items = new ArrayList<>();

    @CreationTimestamp
    private Instant createdAt;

    @UpdateTimestamp
    private Instant updatedAt;
}
```

### Repository pattern

```java
public interface OrderRepository extends JpaRepository<Order, UUID> {

    List<Order> findByCustomerIdAndStatus(UUID customerId, OrderStatus status);

    @Query("SELECT o FROM Order o WHERE o.createdAt >= :since AND o.status = :status")
    List<Order> findRecentByStatus(@Param("since") Instant since, @Param("status") OrderStatus status);
}
```

Use Hypersistence Utils for advanced JPA types (JSON columns, arrays, etc.).

## Rate limiting with Bucket4j

```java
@Configuration
public class RateLimitConfig {

    @Bean
    public Bucket createBucket() {
        Bandwidth limit = Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1)));
        return Bucket.builder().addLimit(limit).build();
    }
}
```

Apply per-endpoint or per-user via a filter or interceptor. Combine with Spring Security to rate-limit by authenticated principal.

## Email with Resend

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class EmailService {

    private final ResendClient resendClient;

    public void sendWelcomeEmail(String to, String name) {
        try {
            CreateEmailOptions options = CreateEmailOptions.builder()
                .from("noreply@example.com")
                .to(to)
                .subject("Welcome, " + name)
                .html(buildWelcomeHtml(name))
                .build();
            resendClient.emails().send(options);
            log.info("Welcome email sent, recipient={}", to);
        } catch (ResendException e) {
            log.error("Failed to send welcome email, recipient={}", to, e);
        }
    }
}
```

## Configuration and secrets management

### application.properties — non-secret config only

```properties
spring.application.name=quantun
server.port=8080
spring.jpa.hibernate.ddl-auto=validate
spring.flyway.enabled=true
spring.flyway.locations=classpath:db/migration
```

### Environment variables for secrets (Railway pattern)

```properties
spring.datasource.url=${DATABASE_URL}
spring.datasource.username=${PGUSER}
spring.datasource.password=${PGPASSWORD}
spring.data.redis.url=${REDIS_URL}
spring.ai.anthropic.api-key=${ANTHROPIC_API_KEY}
spring.ai.openai.api-key=${OPENAI_API_KEY}
app.jwt.secret=${JWT_SECRET}
app.turnstile.secret-key=${TURNSTILE_SECRET_KEY}
```

Never commit secrets to source. Use Railway environment variables or equivalent.

## Testing strategy (Testing Trophy)

Priority order: Integration > Unit > E2E. Use this stack:

| Layer | Tools | Focus |
|-------|-------|-------|
| Integration | Spring Boot Test, `@WebMvcTest`, `@DataJpaTest`, MockMvc, Testcontainers | API contracts, DB queries, service interactions |
| Unit | JUnit 5, Mockito | Business logic in handlers, utility functions |
| E2E | Testcontainers, RestAssured | Full request lifecycle, multi-service flows |

### Integration test example

```java
@WebMvcTest(OrderController.class)
@Import(SecurityConfig.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private CreateOrderHandler createOrderHandler;

    @Test
    @WithMockUser(roles = "PURCHASER")
    void shouldCreateOrder() throws Exception {
        var response = new CreateOrderResponse(UUID.randomUUID(), OrderStatus.PENDING, Instant.now());
        when(createOrderHandler.handle(any())).thenReturn(response);

        mockMvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "customerId": "550e8400-e29b-41d4-a716-446655440000",
                      "items": [{"productId": "...", "quantity": 2}]
                    }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("PENDING"));
    }
}
```

### Role-based test scenarios

Create test fixtures for each role: Super Admin, Admin, Approver, Purchaser. Verify both access and denial:

```java
@Test
@WithMockUser(roles = "PURCHASER")
void purchaserCanCreateOrder() { /* ... */ }

@Test
@WithMockUser(roles = "PURCHASER")
void purchaserCannotApproveOrder() throws Exception {
    mockMvc.perform(post("/api/v1/orders/{id}/approve", orderId))
        .andExpect(status().isForbidden());
}
```

## RestClient usage (Spring 6.1+)

Prefer `RestClient` over `RestTemplate` for new code:

```java
@Configuration
public class ExternalApiConfig {

    @Bean
    public RestClient anthropicAdminClient(
            @Value("${anthropic.admin.api-key}") String apiKey) {
        return RestClient.builder()
            .baseUrl("https://api.anthropic.com/v1")
            .defaultHeader("x-api-key", apiKey)
            .defaultHeader("anthropic-version", "2023-06-01")
            .build();
    }
}
```

Usage with full pagination:

```java
public List<UsageRecord> fetchAllUsage(LocalDate startDate, LocalDate endDate) {
    List<UsageRecord> allRecords = new ArrayList<>();
    String nextCursor = null;

    do {
        UsagePage page = restClient.get()
            .uri(uri -> {
                uri.path("/usage")
                   .queryParam("start_date", startDate)
                   .queryParam("end_date", endDate);
                if (nextCursor != null) uri.queryParam("cursor", nextCursor);
                return uri.build();
            })
            .retrieve()
            .body(UsagePage.class);

        allRecords.addAll(page.data());
        nextCursor = page.nextCursor();
    } while (nextCursor != null);

    return allRecords;
}
```

## MinIO / S3 presigned URLs

Prevent denial-of-wallet attacks by constraining presigned URL parameters:

```java
public String generatePresignedUploadUrl(String objectKey, long maxSizeBytes) {
    PostPolicy policy = new PostPolicy(bucketName, ZonedDateTime.now().plusMinutes(15));
    policy.addEqualsCondition("key", objectKey);
    policy.addContentLengthRangeCondition(1, maxSizeBytes);

    Map<String, String> formData = minioClient.getPresignedPostFormData(policy);
    return buildPresignedUrl(formData);
}
```

## Spring AI bean configuration (multi-model routing)

When using multiple AI providers (e.g., Anthropic for chat + OpenAI for TTS/STT), use explicit bean qualifiers to avoid conflicts:

```java
@Configuration
public class AiConfig {

    @Bean
    @Primary
    ChatClient anthropicChatClient(
            @Qualifier("anthropicChatModel") ChatModel chatModel) {
        return ChatClient.builder(chatModel)
            .defaultSystem(new ClassPathResource("prompts/system/default.st"))
            .build();
    }

    @Bean
    ChatClient openaiChatClient(
            @Qualifier("openAiChatModel") ChatModel chatModel) {
        return ChatClient.builder(chatModel).build();
    }
}
```

For Spring AI audio (TTS/STT), configure model routing explicitly to prevent the wrong model from being injected:

```properties
# Anthropic for chat
spring.ai.anthropic.chat.options.model=claude-sonnet-4-20250514

# OpenAI for TTS and STT only
spring.ai.openai.audio.speech.options.model=gpt-4o-mini-tts
spring.ai.openai.audio.transcription.options.model=whisper-1
```

## Best practices summary

1. **VSA over layered architecture** — features are self-contained, easy to navigate and delete
2. **Records for all DTOs** — immutable, no boilerplate, Jackson-compatible
3. **`@Valid` on all request bodies** — fail fast with clear error messages
4. **`@Transactional` on handler methods** — not on controllers or repositories
5. **Constructor injection via `@RequiredArgsConstructor`** — no field injection
6. **`RestClient` over `RestTemplate`** — modern, fluent, testable
7. **Flyway for every schema change** — no exceptions
8. **Structured logging** — key=value pairs, never string concatenation
9. **Environment variables for secrets** — Railway or equivalent platform
10. **Integration tests first** — they catch the most bugs per effort
11. **Role-based security tests** — verify both access and denial for every endpoint
12. **Servlet/MVC only** — never WebFlux in these projects
