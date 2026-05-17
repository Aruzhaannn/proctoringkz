package kz.proktorai.config;

import kz.proktorai.entity.Role;
import kz.proktorai.entity.User;
import kz.proktorai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        createIfAbsent("student@demo.kz", "demo123", "Айгерім Студент", Role.STUDENT);
        createIfAbsent("teacher@demo.kz", "demo123", "Алмас Оқытушы",   Role.TEACHER);
        createIfAbsent("admin@demo.kz",   "demo123", "Нұрлан Әкімші",   Role.ADMIN);
    }

    private void createIfAbsent(String email, String password, String fullName, Role role) {
        if (!userRepository.existsByEmail(email)) {
            userRepository.save(User.builder()
                    .email(email)
                    .password(passwordEncoder.encode(password))
                    .fullName(fullName)
                    .role(role)
                    .enabled(true)
                    .build());
            log.info("Demo user created: {}", email);
        }
    }
}
