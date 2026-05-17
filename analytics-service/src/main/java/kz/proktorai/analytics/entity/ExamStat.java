package kz.proktorai.analytics.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "exam_stats", schema = "analytics")
@Data
@NoArgsConstructor
public class ExamStat {

    @Id
    private Long examId;

    private String examTitle;

    private int totalSessions = 0;
    private int completedSessions = 0;
    private int terminatedSessions = 0;

    private double totalCheatScoreSum = 0.0;
    private int highRiskSessions = 0;
    private int totalViolations = 0;

    private LocalDateTime lastUpdated;

    public ExamStat(Long examId, String examTitle) {
        this.examId = examId;
        this.examTitle = examTitle;
        this.lastUpdated = LocalDateTime.now();
    }

    public double getAvgCheatScore() {
        if (totalSessions == 0) return 0.0;
        return Math.round((totalCheatScoreSum / totalSessions) * 10.0) / 10.0;
    }

    public double getCompletionRate() {
        if (totalSessions == 0) return 0.0;
        return Math.round(((double) completedSessions / totalSessions) * 1000.0) / 10.0;
    }
}