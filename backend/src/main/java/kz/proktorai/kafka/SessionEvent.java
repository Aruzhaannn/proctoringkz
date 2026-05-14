package kz.proktorai.kafka;

import kz.proktorai.entity.SessionStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SessionEvent {
    private Long sessionId;
    private Long studentId;
    private String studentName;
    private Long examId;
    private String examTitle;
    private SessionStatus status;
    private Integer cheatScore;
    private LocalDateTime eventTime;
}