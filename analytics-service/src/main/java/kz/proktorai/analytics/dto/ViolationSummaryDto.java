package kz.proktorai.analytics.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ViolationSummaryDto {
    private String violationType;
    private long totalCount;
}