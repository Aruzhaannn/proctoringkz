package kz.proktorai.analytics.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import kz.proktorai.analytics.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class SessionEventConsumer {

    private final AnalyticsService analyticsService;
    private final ObjectMapper objectMapper;

    @KafkaListener(topics = "proktorai.sessions", groupId = "analytics-group")
    public void consume(Object payload) {
        try {
            SessionEvent event = objectMapper.convertValue(payload, SessionEvent.class);
            analyticsService.processSessionEvent(event);
        } catch (Exception e) {
            log.error("Failed to process session event: {}", e.getMessage());
        }
    }
}