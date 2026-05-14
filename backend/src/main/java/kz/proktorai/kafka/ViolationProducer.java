package kz.proktorai.kafka;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class ViolationProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${app.kafka.topics.violation}")
    private String topic;

    public void send(ViolationEvent event) {
        kafkaTemplate.send(topic, String.valueOf(event.getSessionId()), event)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        log.error("Violation event send failed: {}", ex.getMessage());
                    } else {
                        log.info("Violation sent → session={} type={} score={}",
                                event.getSessionId(), event.getViolationType(), event.getScore());
                    }
                });
    }
}
