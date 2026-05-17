package kz.proktorai.service;

import kz.proktorai.entity.Question;
import kz.proktorai.entity.QuestionOption;
import kz.proktorai.entity.QuestionType;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

@Service
public class WordParserService {

    /**
     * Parses a Word (.docx) file containing questions.
     * Expected format:
     * 1. What is Java?
     * A) Language
     * B) Animal
     * C) Car
     * D) Food
     * Answer: A
     */
    public List<Question> parseQuestions(MultipartFile file) {
        List<Question> questions = new ArrayList<>();

        try (InputStream is = file.getInputStream();
             XWPFDocument document = new XWPFDocument(is)) {

            Question currentQuestion = null;
            List<QuestionOption> currentOptions = new ArrayList<>();
            int orderIndex = 1;

            for (XWPFParagraph p : document.getParagraphs()) {
                String text = p.getText().trim();
                if (text.isEmpty()) continue;

                // Simple heuristic for question parsing
                // e.g. "1. What is Java?"
                if (text.matches("^\\d+\\..+")) {
                    // Save previous question
                    if (currentQuestion != null && !currentOptions.isEmpty()) {
                        currentQuestion.setOptions(currentOptions);
                        questions.add(currentQuestion);
                    }

                    currentQuestion = Question.builder()
                            .questionText(text.replaceFirst("^\\d+\\.\\s*", "").trim())
                            .questionType(QuestionType.MULTIPLE_CHOICE)
                            .points(1)
                            .orderIndex(orderIndex++)
                            .build();
                    currentOptions = new ArrayList<>();
                }
                // Options: "A) ..." or "a) ..."
                else if (text.matches("^[A-Da-d][\\)\\.].+")) {
                    if (currentQuestion != null) {
                        String optionText = text.substring(2).trim();
                        QuestionOption option = QuestionOption.builder()
                                .optionText(optionText)
                                .isCorrect(false) // will set later
                                .question(currentQuestion)
                                .build();
                        currentOptions.add(option);
                    }
                }
                // Answer: "Answer: A" or "Ответ: A"
                else if (text.toLowerCase().startsWith("answer:") || text.toLowerCase().startsWith("ответ:")) {
                    if (currentQuestion != null && !currentOptions.isEmpty()) {
                        String ansLetter = text.split(":")[1].trim().toUpperCase();
                        int correctIdx = ansLetter.charAt(0) - 'A';
                        if (correctIdx >= 0 && correctIdx < currentOptions.size()) {
                            currentOptions.get(correctIdx).setIsCorrect(true);
                        }
                    }
                }
            }

            // Save the last question
            if (currentQuestion != null && !currentOptions.isEmpty()) {
                currentQuestion.setOptions(currentOptions);
                questions.add(currentQuestion);
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to parse Word document: " + e.getMessage(), e);
        }

        return questions;
    }
}
