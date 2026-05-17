package kz.proktorai.dto.exam;

import kz.proktorai.entity.SessionStatus;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
public class SessionResponse {
    private Long id;
    private Long examId;
    private String examTitle;
    private String studentName;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private SessionStatus status;
    private Integer cheatScore;
    private Boolean phoneUnlocked;
    private List<ViolationResponse> violations;
    private List<SessionQuestionResponse> questions;
}