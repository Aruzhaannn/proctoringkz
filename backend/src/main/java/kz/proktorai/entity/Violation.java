package kz.proktorai.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "violations")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Violation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ExamSession examSession;

    @Column(nullable = false)
    private String type;       // NO_FACE, PHONE_DETECTED, HEAD_TURNED, etc.

    @Column(nullable = false)
    private Integer score;     // violation weight

    @Column(columnDefinition = "TEXT")
    private String details;    // JSON from AI service

    @Column(nullable = false, updatable = false)
    private LocalDateTime detectedAt;

    @PrePersist
    protected void onCreate() {
        detectedAt = LocalDateTime.now();
    }
}