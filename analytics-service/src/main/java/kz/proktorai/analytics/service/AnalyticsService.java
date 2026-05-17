package kz.proktorai.analytics.service;

import kz.proktorai.analytics.entity.ExamStat;
import kz.proktorai.analytics.entity.StudentStat;
import kz.proktorai.analytics.entity.ViolationTypeStat;
import kz.proktorai.analytics.kafka.SessionEvent;
import kz.proktorai.analytics.kafka.ViolationEvent;
import kz.proktorai.analytics.repository.ExamStatRepository;
import kz.proktorai.analytics.repository.StudentStatRepository;
import kz.proktorai.analytics.repository.ViolationTypeStatRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnalyticsService {

    private final ExamStatRepository examStatRepo;
    private final StudentStatRepository studentStatRepo;
    private final ViolationTypeStatRepository violationTypeStatRepo;

    @Transactional
    public void processViolationEvent(ViolationEvent event) {
        updateExamViolationStat(event);
        updateStudentViolationStat(event);
        updateViolationTypeStat(event);
        log.debug("Processed violation event: examId={}, type={}", event.getExamId(), event.getViolationType());
    }

    @Transactional
    public void processSessionEvent(SessionEvent event) {
        if (event.getStatus() == null) return;

        ExamStat exam = examStatRepo.findById(event.getExamId())
                .orElseGet(() -> new ExamStat(event.getExamId(), event.getExamTitle()));

        StudentStat student = studentStatRepo.findById(event.getStudentId())
                .orElseGet(() -> new StudentStat(event.getStudentId(), event.getStudentName()));

        switch (event.getStatus()) {
            case "IN_PROGRESS" -> {
                exam.setTotalSessions(exam.getTotalSessions() + 1);
                student.setTotalExams(student.getTotalExams() + 1);
            }
            case "COMPLETED" -> {
                exam.setCompletedSessions(exam.getCompletedSessions() + 1);
                if (event.getCheatScore() != null) {
                    finalizeSessionScore(exam, student, event.getCheatScore());
                }
            }
            case "TERMINATED" -> {
                exam.setTerminatedSessions(exam.getTerminatedSessions() + 1);
                if (event.getCheatScore() != null) {
                    finalizeSessionScore(exam, student, event.getCheatScore());
                }
            }
        }

        exam.setLastUpdated(LocalDateTime.now());
        student.setLastActivity(LocalDateTime.now());

        examStatRepo.save(exam);
        studentStatRepo.save(student);
        log.debug("Processed session event: examId={}, status={}", event.getExamId(), event.getStatus());
    }

    private void updateExamViolationStat(ViolationEvent event) {
        ExamStat exam = examStatRepo.findById(event.getExamId())
                .orElseGet(() -> new ExamStat(event.getExamId(), event.getExamTitle()));

        exam.setTotalViolations(exam.getTotalViolations() + 1);

        if (event.getTotalCheatScore() != null && event.getTotalCheatScore() >= 70) {
            exam.setHighRiskSessions(exam.getHighRiskSessions() + 1);
        }

        exam.setLastUpdated(LocalDateTime.now());
        examStatRepo.save(exam);
    }

    private void updateStudentViolationStat(ViolationEvent event) {
        StudentStat student = studentStatRepo.findById(event.getStudentId())
                .orElseGet(() -> new StudentStat(event.getStudentId(), event.getStudentName()));

        student.setTotalViolations(student.getTotalViolations() + 1);

        if (event.getTotalCheatScore() != null && event.getTotalCheatScore() >= 70) {
            student.setFlaggedExams(student.getFlaggedExams() + 1);
        }

        student.setLastActivity(LocalDateTime.now());
        studentStatRepo.save(student);
    }

    private void updateViolationTypeStat(ViolationEvent event) {
        ViolationTypeStat stat = violationTypeStatRepo
                .findByExamIdAndViolationType(event.getExamId(), event.getViolationType())
                .orElseGet(() -> new ViolationTypeStat(event.getExamId(), event.getViolationType()));

        stat.setCount(stat.getCount() + 1);
        if (event.getScore() != null) {
            stat.setTotalScore(stat.getTotalScore() + event.getScore());
        }

        violationTypeStatRepo.save(stat);
    }

    private void finalizeSessionScore(ExamStat exam, StudentStat student, int cheatScore) {
        exam.setTotalCheatScoreSum(exam.getTotalCheatScoreSum() + cheatScore);
        student.setTotalCheatScoreSum(student.getTotalCheatScoreSum() + cheatScore);
        if (cheatScore > student.getMaxCheatScore()) {
            student.setMaxCheatScore(cheatScore);
        }
    }

    public List<ExamStat> getAllExamStats() {
        return examStatRepo.findAllOrderByTotalSessionsDesc();
    }

    public ExamStat getExamStat(Long examId) {
        return examStatRepo.findById(examId).orElse(null);
    }

    public List<ViolationTypeStat> getViolationsByExam(Long examId) {
        return violationTypeStatRepo.findByExamIdOrderByCountDesc(examId);
    }

    public List<StudentStat> getAllStudentStats() {
        return studentStatRepo.findAllOrderByViolationsDesc();
    }

    public List<StudentStat> getHighRiskStudents() {
        return studentStatRepo.findHighRiskStudents();
    }

    public StudentStat getStudentStat(Long studentId) {
        return studentStatRepo.findById(studentId).orElse(null);
    }

    public List<Object[]> getGlobalViolationSummary() {
        return violationTypeStatRepo.findGlobalViolationSummary();
    }
}