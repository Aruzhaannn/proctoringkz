package kz.proktorai.kafka;

import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class SessionConsumer {

    @KafkaListener(topics = "${app.kafka.topics.session}", groupId = "${spring.kafka.consumer.group-id}")
    public void consume(SessionEvent event) {
        log.info("[SESSION] id={} student='{}' exam='{}' status={} cheatScore={}",
                event.getSessionId(),
                event.getStudentName(),
                event.getExamTitle(),
                event.getStatus(),
                event.getCheatScore());
    }
}