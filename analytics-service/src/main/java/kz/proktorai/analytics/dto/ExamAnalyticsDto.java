package kz.proktorai.analytics.dto;

import kz.proktorai.analytics.entity.ExamStat;
import kz.proktorai.analytics.entity.ViolationTypeStat;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class ExamAnalyticsDto {

    private Long examId;
    private String examTitle;
    private int totalSessions;
    private int completedSessions;
    private int terminatedSessions;
    private double avgCheatScore;
    private double completionRate;
    private int highRiskSessions;
    private int totalViolations;
    private LocalDateTime lastUpdated;
    private List<ViolationBreakdown> violationBreakdown;

    @Data
    public static class ViolationBreakdown {
        private String violationType;
        private int count;
        private int totalScore;
    }

    public static ExamAnalyticsDto from(ExamStat stat, List<ViolationTypeStat> violations) {
        ExamAnalyticsDto dto = new ExamAnalyticsDto();
        dto.setExamId(stat.getExamId());
        dto.setExamTitle(stat.getExamTitle());
        dto.setTotalSessions(stat.getTotalSessions());
        dto.setCompletedSessions(stat.getCompletedSessions());
        dto.setTerminatedSessions(stat.getTerminatedSessions());
        dto.setAvgCheatScore(stat.getAvgCheatScore());
        dto.setCompletionRate(stat.getCompletionRate());
        dto.setHighRiskSessions(stat.getHighRiskSessions());
        dto.setTotalViolations(stat.getTotalViolations());
        dto.setLastUpdated(stat.getLastUpdated());

        dto.setViolationBreakdown(violations.stream().map(v -> {
            ViolationBreakdown vb = new ViolationBreakdown();
            vb.setViolationType(v.getViolationType());
            vb.setCount(v.getCount());
            vb.setTotalScore(v.getTotalScore());
            return vb;
        }).toList());

        return dto;
    }
}