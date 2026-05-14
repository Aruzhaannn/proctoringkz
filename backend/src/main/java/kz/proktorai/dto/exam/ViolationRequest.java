package kz.proktorai.dto.exam;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ViolationRequest {

    @NotNull
    private Long sessionId;

    @NotBlank
    private String type;

    @NotNull
    private Integer score;

    private String details;
}