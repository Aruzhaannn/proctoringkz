package kz.proktorai.controller;

import jakarta.validation.Valid;
import kz.proktorai.dto.exam.ExamRequest;
import kz.proktorai.dto.exam.ExamResponse;
import kz.proktorai.entity.User;
import kz.proktorai.service.ExamService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/exams")
@RequiredArgsConstructor
public class ExamController {

    private final ExamService examService;

    // Teacher/Admin — емтихан жасау
    @PostMapping
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<ExamResponse> create(
            @Valid @RequestBody ExamRequest request,
            @AuthenticationPrincipal User teacher) {
        return ResponseEntity.ok(examService.create(request, teacher));
    }

    // Teacher/Admin — белсендіру
    @PatchMapping("/{id}/activate")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<ExamResponse> activate(
            @PathVariable Long id,
            @AuthenticationPrincipal User teacher) {
        return ResponseEntity.ok(examService.activate(id, teacher));
    }

    // Teacher/Admin — аяқтау
    @PatchMapping("/{id}/finish")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<ExamResponse> finish(
            @PathVariable Long id,
            @AuthenticationPrincipal User teacher) {
        return ResponseEntity.ok(examService.finish(id, teacher));
    }

    // Барлығы — белсенді емтихандар тізімі
    @GetMapping("/active")
    public ResponseEntity<List<ExamResponse>> getActive() {
        return ResponseEntity.ok(examService.getActive());
    }

    // Teacher/Admin — өзінің емтихандары
    @GetMapping("/my")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public ResponseEntity<List<ExamResponse>> getMine(@AuthenticationPrincipal User teacher) {
        return ResponseEntity.ok(examService.getByTeacher(teacher));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ExamResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(examService.getById(id));
    }

    // Барлық пайдаланушылар — барлық емтихандарды көре алады (кесте үшін)
    @GetMapping
    public ResponseEntity<List<ExamResponse>> getAll() {
        return ResponseEntity.ok(examService.getAll());
    }
}