package kz.proktorai.repository;

import kz.proktorai.entity.ExamSession;
import kz.proktorai.entity.SessionStatus;
import kz.proktorai.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ExamSessionRepository extends JpaRepository<ExamSession, Long> {
    List<ExamSession> findByStudent(User student);
    List<ExamSession> findByExamId(Long examId);
    List<ExamSession> findByStatus(SessionStatus status);
    Optional<ExamSession> findByIdAndStudent(Long id, User student);
}