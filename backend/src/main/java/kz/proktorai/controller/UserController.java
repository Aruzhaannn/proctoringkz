package kz.proktorai.controller;

import kz.proktorai.dto.UserResponse;
import kz.proktorai.entity.Role;
import kz.proktorai.entity.User;
import kz.proktorai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@CrossOrigin(origins = "*", maxAge = 3600)
public class UserController {

    private final UserRepository userRepository;

    @GetMapping("/students")
    @PreAuthorize("hasAnyRole('ADMIN', 'TEACHER')")
    public ResponseEntity<List<UserResponse>> getStudents() {
        List<User> students = userRepository.findByRole(Role.STUDENT);
        List<UserResponse> responses = students.stream().map(u -> UserResponse.builder()
                .id(u.getId())
                .email(u.getEmail())
                .fullName(u.getFullName())
                .role(u.getRole())
                .build()).collect(Collectors.toList());
        return ResponseEntity.ok(responses);
    }
}
