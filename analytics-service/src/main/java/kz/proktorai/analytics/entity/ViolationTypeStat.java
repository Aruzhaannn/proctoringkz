package kz.proktorai.analytics.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(
    name = "violation_type_stats",
    schema = "analytics",
    uniqueConstraints = @UniqueConstraint(columnNames = {"examId", "violationType"})
)
@Data
@NoArgsConstructor
public class ViolationTypeStat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long examId;
    private String violationType;
    private int count = 0;
    private int totalScore = 0;

    public ViolationTypeStat(Long examId, String violationType) {
        this.examId = examId;
        this.violationType = violationType;
    }
}