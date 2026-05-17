package kz.proktorai.dto;

import lombok.Data;

@Data
public class AuditLogRequest {
    private String action;
    private Long   sessionId;
    private String details;
    private String browserInfo;
}
