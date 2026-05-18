package kz.proktorai.service;

import kz.proktorai.dto.exam.ExamRequest;
import kz.proktorai.dto.exam.ExamResponse;
import kz.proktorai.entity.Exam;
import kz.proktorai.entity.ExamStatus;
import kz.proktorai.entity.User;
import kz.proktorai.repository.ExamRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ExamService {

    private final ExamRepository examRepository;
    private final kz.proktorai.repository.StudentGroupRepository groupRepository;
    private final kz.proktorai.repository.QuestionRepository questionRepository;
    private final WordParserService wordParserService;

    @CacheEvict(value = "exams", allEntries = true)
    public ExamResponse create(ExamRequest request, org.springframework.web.multipart.MultipartFile file, User teacher) {
        kz.proktorai.entity.StudentGroup group = null;
        if (request.getGroupId() != null) {
            group = groupRepository.findById(request.getGroupId())
                    .orElseThrow(() -> new IllegalArgumentException("Group not found"));
        }

        var exam = Exam.builder()
                .title(request.getTitle())
                .description(request.getDescription())
                .durationMinutes(request.getDurationMinutes())
                .startTime(request.getStartTime())
                .endTime(request.getEndTime())
                .createdBy(teacher)
                .targetGroup(group)
                .totalQuestions(request.getTotalQuestions() != null ? request.getTotalQuestions() : 0)
                .passingScore(request.getPassingScore())
                .build();
        
        exam = examRepository.save(exam);

        if (file != null && !file.isEmpty()) {
            List<kz.proktorai.entity.Question> questions = wordParserService.parseQuestions(file);
            for (kz.proktorai.entity.Question q : questions) {
                q.setExam(exam);
            }
            questionRepository.saveAll(questions);
        }

        return toResponse(exam);
    }

    @CacheEvict(value = "exams", allEntries = true)
    public ExamResponse activate(Long id, User teacher) {
        var exam = getExamOwnedBy(id, teacher);
        exam.setStatus(ExamStatus.ACTIVE);
        return toResponse(examRepository.save(exam));
    }

    @CacheEvict(value = "exams", allEntries = true)
    public ExamResponse finish(Long id, User teacher) {
        var exam = getExamOwnedBy(id, teacher);
        exam.setStatus(ExamStatus.FINISHED);
        return toResponse(examRepository.save(exam));
    }

    public List<ExamResponse> getAll() {
        return examRepository.findAll().stream().map(this::toResponse).toList();
    }

    public List<ExamResponse> getActive() {
        return examRepository.findByStatus(ExamStatus.ACTIVE).stream().map(this::toResponse).toList();
    }

    public List<ExamResponse> getByTeacher(User teacher) {
        return examRepository.findByCreatedBy(teacher).stream().map(this::toResponse).toList();
    }

    @Cacheable(value = "exams", key = "#id")
    public ExamResponse getById(Long id) {
        return toResponse(findById(id));
    }

    public Exam findById(Long id) {
        return examRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Exam not found: " + id));
    }

    private Exam getExamOwnedBy(Long id, User teacher) {
        var exam = findById(id);
        if (!exam.getCreatedBy().getId().equals(teacher.getId())) {
            throw new IllegalArgumentException("Access denied");
        }
        return exam;
    }

    private ExamResponse toResponse(Exam e) {
        return ExamResponse.builder()
                .id(e.getId())
                .title(e.getTitle())
                .description(e.getDescription())
                .durationMinutes(e.getDurationMinutes())
                .startTime(e.getStartTime())
                .endTime(e.getEndTime())
                .status(e.getStatus())
                .createdByName(e.getCreatedBy().getFullName())
                .createdAt(e.getCreatedAt())
                .groupId(e.getTargetGroup() != null ? e.getTargetGroup().getId() : null)
                .groupName(e.getTargetGroup() != null ? e.getTargetGroup().getName() : null)
                .totalQuestions(e.getTotalQuestions())
                .passingScore(e.getPassingScore())
                .build();
    }
}