package kz.proktorai.analytics.repository;

import kz.proktorai.analytics.entity.ExamStat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ExamStatRepository extends JpaRepository<ExamStat, Long> {

    @Query("SELECT e FROM ExamStat e ORDER BY e.totalSessions DESC")
    List<ExamStat> findAllOrderByTotalSessionsDesc();

    @Query("SELECT e FROM ExamStat e WHERE e.highRiskSessions > 0 ORDER BY e.highRiskSessions DESC")
    List<ExamStat> findExamsWithHighRisk();
}