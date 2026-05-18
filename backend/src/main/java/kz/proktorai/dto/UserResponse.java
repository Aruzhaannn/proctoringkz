package kz.proktorai.dto;

import kz.proktorai.entity.Role;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserResponse {
    private Long id;
    private String email;
    private String fullName;
    private Role role;
}
