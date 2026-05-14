package kz.proktorai.repository;

import kz.proktorai.entity.Exam;
import kz.proktorai.entity.ExamStatus;
import kz.proktorai.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ExamRepository extends JpaRepository<Exam, Long> {
    List<Exam> findByCreatedBy(User teacher);
    List<Exam> findByStatus(ExamStatus status);
}