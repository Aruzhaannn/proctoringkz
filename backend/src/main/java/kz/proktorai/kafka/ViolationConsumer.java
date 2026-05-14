package kz.proktorai.kafka;

import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class ViolationConsumer {

    @KafkaListener(topics = "${app.kafka.topics.violation}", groupId = "${spring.kafka.consumer.group-id}")
    public void consume(ViolationEvent event) {
        log.info("[VIOLATION] session={} student='{}' type={} score={} total={}",
                event.getSessionId(),
                event.getStudentName(),
                event.getViolationType(),
                event.getScore(),
                event.getTotalCheatScore());

        // HIGH RISK — мұғалімге хабарлама жіберу (Kafka → Teacher notification)
        if (event.getTotalCheatScore() != null && event.getTotalCheatScore() >= 70) {
            log.warn("[HIGH RISK] Student '{}' cheatScore={} in exam '{}'",
                    event.getStudentName(), event.getTotalCheatScore(), event.getExamTitle());
        }
    }
}