package kz.proktorai.dto.exam;

import kz.proktorai.entity.QuestionOption;
import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class SessionQuestionResponse {
    private Long id;
    private Long questionId;
    private String text;
    private List<OptionResponse> options;
    private String studentAnswer;
    
    @Data
    @Builder
    public static class OptionResponse {
        private Long id;
        private String text;
    }
}
