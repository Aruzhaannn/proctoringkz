package kz.proktorai.analytics.kafka;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
public class ViolationEvent {
    private Long sessionId;
    private Long studentId;
    private String studentName;
    private Long examId;
    private String examTitle;
    private String violationType;
    private Integer score;
    private Integer totalCheatScore;
    private String details;
    private LocalDateTime detectedAt;
}