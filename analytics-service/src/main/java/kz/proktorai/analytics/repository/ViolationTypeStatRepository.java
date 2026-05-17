package kz.proktorai.analytics.repository;

import kz.proktorai.analytics.entity.ViolationTypeStat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface ViolationTypeStatRepository extends JpaRepository<ViolationTypeStat, Long> {

    Optional<ViolationTypeStat> findByExamIdAndViolationType(Long examId, String violationType);

    List<ViolationTypeStat> findByExamIdOrderByCountDesc(Long examId);

    @Query("SELECT v.violationType, SUM(v.count) as total FROM ViolationTypeStat v GROUP BY v.violationType ORDER BY total DESC")
    List<Object[]> findGlobalViolationSummary();
}