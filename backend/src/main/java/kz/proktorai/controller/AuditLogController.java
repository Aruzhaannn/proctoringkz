package kz.proktorai.controller;

import jakarta.servlet.http.HttpServletRequest;
import kz.proktorai.dto.AuditLogRequest;
import kz.proktorai.dto.AuditLogResponse;
import kz.proktorai.entity.AuditLog;
import kz.proktorai.entity.User;
import kz.proktorai.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/audit")
@RequiredArgsConstructor
public class AuditLogController {

    private final AuditLogRepository auditLogRepository;

    @PostMapping
    public ResponseEntity<AuditLogResponse> log(
            @RequestBody AuditLogRequest request,
            @AuthenticationPrincipal User user,
            HttpServletRequest httpRequest) {

        String ip = httpRequest.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank()) ip = httpRequest.getRemoteAddr();

        var log = AuditLog.builder()
                .action(request.getAction())
                .sessionId(request.getSessionId())
                .performedBy(user != null ? user.getEmail() : "system")
                .details(request.getDetails())
                .ipAddress(ip)
                .browserInfo(request.getBrowserInfo() != null
                        ? request.getBrowserInfo().substring(0, Math.min(request.getBrowserInfo().length(), 256))
                        : null)
                .build();

        var saved = auditLogRepository.save(log);
        return ResponseEntity.ok(toResponse(saved));
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public List<AuditLogResponse> getAll() {
        return auditLogRepository.findTop100ByOrderByCreatedAtDesc()
                .stream().map(this::toResponse).toList();
    }

    @GetMapping("/session/{sessionId}")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public List<AuditLogResponse> getBySession(@PathVariable Long sessionId) {
        return auditLogRepository.findBySessionIdOrderByCreatedAtDesc(sessionId)
                .stream().map(this::toResponse).toList();
    }

    private AuditLogResponse toResponse(AuditLog l) {
        return AuditLogResponse.builder()
                .id(l.getId())
                .action(l.getAction())
                .sessionId(l.getSessionId())
                .performedBy(l.getPerformedBy())
                .details(l.getDetails())
                .ipAddress(l.getIpAddress())
                .browserInfo(l.getBrowserInfo())
                .createdAt(l.getCreatedAt())
                .build();
    }
}
