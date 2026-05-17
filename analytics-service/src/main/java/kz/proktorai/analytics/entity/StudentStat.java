package kz.proktorai.analytics.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "student_stats", schema = "analytics")
@Data
@NoArgsConstructor
public class StudentStat {

    @Id
    private Long studentId;

    private String studentName;

    private int totalExams = 0;
    private double totalCheatScoreSum = 0.0;
    private int maxCheatScore = 0;
    private int totalViolations = 0;
    private int flaggedExams = 0;

    private LocalDateTime lastActivity;

    public StudentStat(Long studentId, String studentName) {
        this.studentId = studentId;
        this.studentName = studentName;
        this.lastActivity = LocalDateTime.now();
    }

    public double getAvgCheatScore() {
        if (totalExams == 0) return 0.0;
        return Math.round((totalCheatScoreSum / totalExams) * 10.0) / 10.0;
    }
}