package kz.proktorai.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "audit_logs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 64)
    private String action;          // PHONE_DETECTED, SESSION_TERMINATED, TAB_SWITCH, etc.

    @Column(name = "session_id")
    private Long sessionId;

    @Column(name = "performed_by", length = 128)
    private String performedBy;     // email of teacher/system

    @Column(length = 512)
    private String details;

    @Column(name = "ip_address", length = 64)
    private String ipAddress;

    @Column(name = "browser_info", length = 256)
    private String browserInfo;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
