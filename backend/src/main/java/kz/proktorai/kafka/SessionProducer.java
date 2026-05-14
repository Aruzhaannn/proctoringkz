package kz.proktorai.kafka;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class SessionProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${app.kafka.topics.session}")
    private String topic;

    public void send(SessionEvent event) {
        kafkaTemplate.send(topic, String.valueOf(event.getSessionId()), event)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        log.error("Session event send failed: {}", ex.getMessage());
                    } else {
                        log.info("Session event → id={} status={} cheatScore={}",
                                event.getSessionId(), event.getStatus(), event.getCheatScore());
                    }
                });
    }
}