package kz.proktorai.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "exam_sessions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExamSession {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id", nullable = false)
    private User student;

    @Column(nullable = false, updatable = false)
    private LocalDateTime startTime;

    private LocalDateTime endTime;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private SessionStatus status = SessionStatus.IN_PROGRESS;

    @Column(nullable = false)
    @Builder.Default
    private Integer cheatScore = 0;

    @Column(nullable = false)
    @Builder.Default
    private Boolean phoneUnlocked = false;

    @OneToMany(mappedBy = "examSession", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Violation> violations = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        startTime = LocalDateTime.now();
    }
}