package kz.proktorai.dto.exam;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ExamRequest {

    @NotBlank
    private String title;

    private String description;

    @NotNull
    @Min(1)
    private Integer durationMinutes;

    private LocalDateTime startTime;
    private LocalDateTime endTime;
}