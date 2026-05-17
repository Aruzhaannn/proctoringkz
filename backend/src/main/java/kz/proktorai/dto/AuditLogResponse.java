package kz.proktorai.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class AuditLogResponse {
    private Long          id;
    private String        action;
    private Long          sessionId;
    private String        performedBy;
    private String        details;
    private String        ipAddress;
    private String        browserInfo;
    private LocalDateTime createdAt;
}
