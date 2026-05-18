import java.io.FileInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.Scanner;
public class TestWord {
    public static void main(String[] args) throws Exception {
        ZipInputStream zis = new ZipInputStream(new FileInputStream("c:/Users/Aliakbar/Documents/GitHub/proctoringkz/exam_15_questions.docx"));
        ZipEntry entry;
        while((entry = zis.getNextEntry()) != null) {
            if(entry.getName().equals("word/document.xml")) {
                Scanner s = new Scanner(zis).useDelimiter("\\A");
                System.out.println(s.hasNext() ? s.next() : "");
            }
        }
    }
}
