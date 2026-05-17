package kz.proktorai.dto.exam;

import lombok.Data;
import java.util.Map;

@Data
public class SubmitAnswersRequest {
    // Map of SessionQuestionId -> selectedOptionText
    private Map<Long, String> answers;
}
