package kz.proktorai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "session_questions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SessionQuestion {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ExamSession session;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "question_id", nullable = false)
    private Question question;

    @Column(columnDefinition = "TEXT")
    private String studentAnswer;

    private Boolean isCorrect;
    
    @Builder.Default
    private Integer scoreEarned = 0;
}
