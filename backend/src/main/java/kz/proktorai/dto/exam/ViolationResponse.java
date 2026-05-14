package kz.proktorai.dto.exam;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ViolationResponse {
    private Long id;
    private String type;
    private Integer score;
    private String details;
    private LocalDateTime detectedAt;
}