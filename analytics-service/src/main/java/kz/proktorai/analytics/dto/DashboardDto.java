package kz.proktorai.analytics.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class DashboardDto {
    private int totalExams;
    private int totalSessions;
    private int totalViolations;
    private int highRiskStudents;
    private double overallAvgCheatScore;
    private List<ViolationSummaryDto> topViolations;
}