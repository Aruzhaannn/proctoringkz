package kz.proktorai.analytics.repository;

import kz.proktorai.analytics.entity.StudentStat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface StudentStatRepository extends JpaRepository<StudentStat, Long> {

    @Query("SELECT s FROM StudentStat s WHERE s.flaggedExams > 0 ORDER BY s.flaggedExams DESC")
    List<StudentStat> findHighRiskStudents();

    @Query("SELECT s FROM StudentStat s ORDER BY s.totalViolations DESC")
    List<StudentStat> findAllOrderByViolationsDesc();
}