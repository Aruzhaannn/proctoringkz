package kz.proktorai.analytics.controller;

import kz.proktorai.analytics.dto.DashboardDto;
import kz.proktorai.analytics.dto.ExamAnalyticsDto;
import kz.proktorai.analytics.dto.StudentAnalyticsDto;
import kz.proktorai.analytics.dto.ViolationSummaryDto;
import kz.proktorai.analytics.entity.ExamStat;
import kz.proktorai.analytics.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/analytics")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/dashboard")
    public ResponseEntity<DashboardDto> getDashboard() {
        List<ExamStat> exams = analyticsService.getAllExamStats();

        int totalSessions = exams.stream().mapToInt(ExamStat::getTotalSessions).sum();
        int totalViolations = exams.stream().mapToInt(ExamStat::getTotalViolations).sum();
        int highRiskStudents = analyticsService.getHighRiskStudents().size();

        double avgCheatScore = exams.stream()
                .filter(e -> e.getTotalSessions() > 0)
                .mapToDouble(ExamStat::getAvgCheatScore)
                .average()
                .orElse(0.0);

        List<ViolationSummaryDto> topViolations = analyticsService.getGlobalViolationSummary().stream()
                .limit(5)
                .map(row -> new ViolationSummaryDto((String) row[0], ((Number) row[1]).longValue()))
                .toList();

        DashboardDto dashboard = DashboardDto.builder()
                .totalExams(exams.size())
                .totalSessions(totalSessions)
                .totalViolations(totalViolations)
                .highRiskStudents(highRiskStudents)
                .overallAvgCheatScore(Math.round(avgCheatScore * 10.0) / 10.0)
                .topViolations(topViolations)
                .build();

        return ResponseEntity.ok(dashboard);
    }

    @GetMapping("/exams")
    public ResponseEntity<List<ExamAnalyticsDto>> getAllExams() {
        List<ExamAnalyticsDto> result = analyticsService.getAllExamStats().stream()
                .map(stat -> ExamAnalyticsDto.from(stat, analyticsService.getViolationsByExam(stat.getExamId())))
                .toList();
        return ResponseEntity.ok(result);
    }

    @GetMapping("/exams/{examId}")
    public ResponseEntity<ExamAnalyticsDto> getExam(@PathVariable Long examId) {
        ExamStat stat = analyticsService.getExamStat(examId);
        if (stat == null) return ResponseEntity.notFound().build();

        return ResponseEntity.ok(
                ExamAnalyticsDto.from(stat, analyticsService.getViolationsByExam(examId))
        );
    }

    @GetMapping("/students")
    public ResponseEntity<List<StudentAnalyticsDto>> getAllStudents() {
        List<StudentAnalyticsDto> result = analyticsService.getAllStudentStats().stream()
                .map(StudentAnalyticsDto::from)
                .toList();
        return ResponseEntity.ok(result);
    }

    @GetMapping("/students/high-risk")
    public ResponseEntity<List<StudentAnalyticsDto>> getHighRiskStudents() {
        List<StudentAnalyticsDto> result = analyticsService.getHighRiskStudents().stream()
                .map(StudentAnalyticsDto::from)
                .toList();
        return ResponseEntity.ok(result);
    }

    @GetMapping("/students/{studentId}")
    public ResponseEntity<StudentAnalyticsDto> getStudent(@PathVariable Long studentId) {
        var stat = analyticsService.getStudentStat(studentId);
        if (stat == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(StudentAnalyticsDto.from(stat));
    }

    @GetMapping("/violations/summary")
    public ResponseEntity<List<ViolationSummaryDto>> getViolationSummary() {
        List<ViolationSummaryDto> result = analyticsService.getGlobalViolationSummary().stream()
                .map(row -> new ViolationSummaryDto((String) row[0], ((Number) row[1]).longValue()))
                .toList();
        return ResponseEntity.ok(result);
    }
}