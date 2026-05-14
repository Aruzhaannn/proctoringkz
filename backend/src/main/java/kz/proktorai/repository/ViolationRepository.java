package kz.proktorai.repository;

import kz.proktorai.entity.Violation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ViolationRepository extends JpaRepository<Violation, Long> {
    List<Violation> findByExamSessionId(Long sessionId);

    @Query("SELECT COUNT(v) FROM Violation v WHERE v.examSession.id = :sessionId AND v.type = :type")
    long countBySessionAndType(Long sessionId, String type);
}