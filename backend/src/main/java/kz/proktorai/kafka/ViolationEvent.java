package kz.proktorai.kafka;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
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