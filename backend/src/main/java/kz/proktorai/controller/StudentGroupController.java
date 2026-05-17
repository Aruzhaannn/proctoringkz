package kz.proktorai.controller;

import kz.proktorai.entity.StudentGroup;
import kz.proktorai.repository.StudentGroupRepository;
import kz.proktorai.repository.UserRepository;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/groups")
@RequiredArgsConstructor
public class StudentGroupController {

    private final StudentGroupRepository groupRepository;
    private final UserRepository userRepository;

    @GetMapping
    public ResponseEntity<List<StudentGroup>> getAllGroups() {
        return ResponseEntity.ok(groupRepository.findAll());
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<StudentGroup> createGroup(@RequestBody GroupRequest request) {
        StudentGroup group = StudentGroup.builder().name(request.getName()).build();
        return ResponseEntity.ok(groupRepository.save(group));
    }

    @PostMapping("/{id}/students")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<?> addStudentsToGroup(@PathVariable Long id, @RequestBody StudentListRequest request) {
        StudentGroup group = groupRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Group not found"));

        for (Long studentId : request.getStudentIds()) {
            userRepository.findById(studentId).ifPresent(user -> {
                user.setStudentGroup(group);
                userRepository.save(user);
            });
        }
        return ResponseEntity.ok("Students added successfully");
    }

    @Data
    public static class GroupRequest {
        private String name;
    }

    @Data
    public static class StudentListRequest {
        private List<Long> studentIds;
    }
}
