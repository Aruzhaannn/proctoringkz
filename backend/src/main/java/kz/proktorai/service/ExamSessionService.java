package kz.proktorai.service;

import kz.proktorai.dto.exam.SessionResponse;
import kz.proktorai.dto.exam.ViolationRequest;
import kz.proktorai.dto.exam.ViolationResponse;
import kz.proktorai.entity.*;
import kz.proktorai.kafka.SessionEvent;
import kz.proktorai.kafka.SessionProducer;
import kz.proktorai.kafka.ViolationEvent;
import kz.proktorai.kafka.ViolationProducer;
import kz.proktorai.repository.ExamSessionRepository;
import kz.proktorai.repository.ViolationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ExamSessionService {

    private final ExamSessionRepository sessionRepository;
    private final ViolationRepository violationRepository;
    private final ExamService examService;
    private final ViolationProducer violationProducer;
    private final SessionProducer sessionProducer;

    @Transactional
    public SessionResponse startSession(Long examId, User student) {
        var exam = examService.findById(examId);
        if (exam.getStatus() != ExamStatus.ACTIVE) {
            throw new IllegalStateException("Exam is not active");
        }
        var session = ExamSession.builder()
                .exam(exam)
                .student(student)
                .build();
        var saved = sessionRepository.save(session);

        sessionProducer.send(SessionEvent.builder()
                .sessionId(saved.getId())
                .studentId(student.getId())
                .studentName(student.getFullName())
                .examId(exam.getId())
                .examTitle(exam.getTitle())
                .status(SessionStatus.IN_PROGRESS)
                .cheatScore(0)
                .eventTime(LocalDateTime.now())
                .build());

        return toResponse(saved);
    }

    @Transactional
    public SessionResponse finishSession(Long sessionId, User student) {
        var session = getSessionForStudent(sessionId, student);
        session.setStatus(SessionStatus.COMPLETED);
        session.setEndTime(LocalDateTime.now());
        var saved = sessionRepository.save(session);

        sessionProducer.send(buildSessionEvent(saved));
        return toResponse(saved);
    }

    @Transactional
    public SessionResponse terminateSession(Long sessionId) {
        var session = findById(sessionId);
        session.setStatus(SessionStatus.TERMINATED);
        session.setEndTime(LocalDateTime.now());
        var saved = sessionRepository.save(session);

        sessionProducer.send(buildSessionEvent(saved));
        return toResponse(saved);
    }

    @Transactional
    public ViolationResponse addViolation(ViolationRequest request) {
        var session = findById(request.getSessionId());

        var violation = Violation.builder()
                .examSession(session)
                .type(request.getType())
                .score(request.getScore())
                .details(request.getDetails())
                .build();

        violationRepository.save(violation);

        int totalScore = violationRepository.findByExamSessionId(session.getId())
                .stream().mapToInt(Violation::getScore).sum();
        session.setCheatScore(Math.min(totalScore, 100));
        sessionRepository.save(session);

        violationProducer.send(ViolationEvent.builder()
                .sessionId(session.getId())
                .studentId(session.getStudent().getId())
                .studentName(session.getStudent().getFullName())
                .examId(session.getExam().getId())
                .examTitle(session.getExam().getTitle())
                .violationType(violation.getType())
                .score(violation.getScore())
                .totalCheatScore(session.getCheatScore())
                .details(violation.getDetails())
                .detectedAt(violation.getDetectedAt())
                .build());

        return toViolationResponse(violation);
    }

    public SessionResponse getSession(Long sessionId) {
        return toResponse(findById(sessionId));
    }

    public List<SessionResponse> getMySessions(User student) {
        return sessionRepository.findByStudent(student).stream().map(this::toResponse).toList();
    }

    public List<SessionResponse> getSessionsByExam(Long examId) {
        return sessionRepository.findByExamId(examId).stream().map(this::toResponse).toList();
    }

    public List<ViolationResponse> getViolations(Long sessionId) {
        return violationRepository.findByExamSessionId(sessionId)
                .stream().map(this::toViolationResponse).toList();
    }

    private ExamSession findById(Long id) {
        return sessionRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Session not found: " + id));
    }

    private ExamSession getSessionForStudent(Long id, User student) {
        return sessionRepository.findByIdAndStudent(id, student)
                .orElseThrow(() -> new IllegalArgumentException("Session not found"));
    }

    private SessionResponse toResponse(ExamSession s) {
        return SessionResponse.builder()
                .id(s.getId())
                .examId(s.getExam().getId())
                .examTitle(s.getExam().getTitle())
                .studentName(s.getStudent().getFullName())
                .startTime(s.getStartTime())
                .endTime(s.getEndTime())
                .status(s.getStatus())
                .cheatScore(s.getCheatScore())
                .violations(s.getViolations().stream().map(this::toViolationResponse).toList())
                .build();
    }

    private SessionEvent buildSessionEvent(ExamSession s) {
        return SessionEvent.builder()
                .sessionId(s.getId())
                .studentId(s.getStudent().getId())
                .studentName(s.getStudent().getFullName())
                .examId(s.getExam().getId())
                .examTitle(s.getExam().getTitle())
                .status(s.getStatus())
                .cheatScore(s.getCheatScore())
                .eventTime(LocalDateTime.now())
                .build();
    }

    private ViolationResponse toViolationResponse(Violation v) {
        return ViolationResponse.builder()
                .id(v.getId())
                .type(v.getType())
                .score(v.getScore())
                .details(v.getDetails())
                .detectedAt(v.getDetectedAt())
                .build();
    }
}