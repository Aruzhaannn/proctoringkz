package kz.proktorai.controller;

import jakarta.validation.Valid;
import kz.proktorai.dto.exam.SessionResponse;
import kz.proktorai.dto.exam.ViolationRequest;
import kz.proktorai.dto.exam.ViolationResponse;
import kz.proktorai.entity.User;
import kz.proktorai.service.ExamSessionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/sessions")
@RequiredArgsConstructor
public class ExamSessionController {

    private final ExamSessionService sessionService;

    // Student — емтиханды бастау
    @PostMapping("/start/{examId}")
    @PreAuthorize("hasRole('STUDENT')")
    public ResponseEntity<SessionResponse> start(
            @PathVariable Long examId,
            @AuthenticationPrincipal User student) {
        return ResponseEntity.ok(sessionService.startSession(examId, student));
    }

    // Student — емтиханды аяқтау
    @PatchMapping("/{id}/finish")
    @PreAuthorize("hasRole('STUDENT')")
    public ResponseEntity<SessionResponse> finish(
            @PathVariable Long id,
            @AuthenticationPrincipal User student) {
        return ResponseEntity.ok(sessionService.finishSession(id, student));
    }

    // Teacher/Admin — сессияны мәжбүрлі тоқтату
    @PatchMapping("/{id}/terminate")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<SessionResponse> terminate(@PathVariable Long id) {
        return ResponseEntity.ok(sessionService.terminateSession(id));
    }

    // AI Service — бұзушылық қосу
    @PostMapping("/violations")
    public ResponseEntity<ViolationResponse> addViolation(
            @Valid @RequestBody ViolationRequest request) {
        return ResponseEntity.ok(sessionService.addViolation(request));
    }

    // Student — өзінің сессиялары
    @GetMapping("/my")
    @PreAuthorize("hasRole('STUDENT')")
    public ResponseEntity<List<SessionResponse>> mySessions(
            @AuthenticationPrincipal User student) {
        return ResponseEntity.ok(sessionService.getMySessions(student));
    }

    // Teacher/Admin — емтиханның барлық сессиялары
    @GetMapping("/exam/{examId}")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<List<SessionResponse>> byExam(@PathVariable Long examId) {
        return ResponseEntity.ok(sessionService.getSessionsByExam(examId));
    }

    @GetMapping("/{id}")
    public ResponseEntity<SessionResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(sessionService.getSession(id));
    }

    // Teacher/Admin — сессияның бұзушылықтары
    @GetMapping("/{id}/violations")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<List<ViolationResponse>> getViolations(@PathVariable Long id) {
        return ResponseEntity.ok(sessionService.getViolations(id));
    }
}