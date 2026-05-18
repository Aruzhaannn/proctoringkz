import org.apache.poi.xwpf.usermodel.XWPFDocument;
import java.io.FileInputStream;
public class TestCrash {
    public static void main(String[] args) {
        try {
            XWPFDocument document = new XWPFDocument(new FileInputStream("c:/Users/Aliakbar/Documents/GitHub/proctoringkz/exam_15_questions.docx"));
            System.out.println("Success! Paragraphs: " + document.getParagraphs().size());
        } catch (Throwable e) {
            e.printStackTrace();
        }
    }
}
