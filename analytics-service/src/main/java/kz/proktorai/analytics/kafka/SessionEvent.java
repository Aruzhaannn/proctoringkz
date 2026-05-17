package kz.proktorai.analytics.kafka;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
public class SessionEvent {
    private Long sessionId;
    private Long studentId;
    private String studentName;
    private Long examId;
    private String examTitle;
    private String status;
    private Integer cheatScore;
    private LocalDateTime eventTime;
}