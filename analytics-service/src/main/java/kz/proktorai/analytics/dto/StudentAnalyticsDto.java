package kz.proktorai.analytics.dto;

import kz.proktorai.analytics.entity.StudentStat;
import lombok.Data;

import java.time.LocalDateTime;

@Data
public class StudentAnalyticsDto {

    private Long studentId;
    private String studentName;
    private int totalExams;
    private double avgCheatScore;
    private int maxCheatScore;
    private int totalViolations;
    private int flaggedExams;
    private String riskLevel;
    private LocalDateTime lastActivity;

    public static StudentAnalyticsDto from(StudentStat stat) {
        StudentAnalyticsDto dto = new StudentAnalyticsDto();
        dto.setStudentId(stat.getStudentId());
        dto.setStudentName(stat.getStudentName());
        dto.setTotalExams(stat.getTotalExams());
        dto.setAvgCheatScore(stat.getAvgCheatScore());
        dto.setMaxCheatScore(stat.getMaxCheatScore());
        dto.setTotalViolations(stat.getTotalViolations());
        dto.setFlaggedExams(stat.getFlaggedExams());
        dto.setLastActivity(stat.getLastActivity());

        double avg = stat.getAvgCheatScore();
        if (avg >= 70) dto.setRiskLevel("HIGH");
        else if (avg >= 40) dto.setRiskLevel("MEDIUM");
        else dto.setRiskLevel("LOW");

        return dto;
    }
}