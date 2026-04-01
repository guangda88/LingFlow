import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 示例 5: Java 客户端
 */
public class LingFlowClient {

    private static final String API_BASE = "http://localhost:8000";
    private static final String API_KEY = "dev-key-12345";
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private final HttpClient client;

    public LingFlowClient() {
        this.client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    }

    // 1. 列出技能
    public Map<String, Object> listSkills() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_BASE + "/api/v1/skills"))
            .header("X-API-Key", API_KEY)
            .GET()
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        return objectMapper.readValue(response.body(), Map.class);
    }

    // 2. 执行技能
    public Map<String, Object> executeSkill(String skillName, Map<String, Object> params) throws Exception {
        Map<String, Object> payload = Map.of(
            "params", params,
            "timeout", 300
        );

        String jsonBody = objectMapper.writeValueAsString(payload);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_BASE + "/api/v1/skills/" + skillName + "/execute"))
            .header("X-API-Key", API_KEY)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        return objectMapper.readValue(response.body(), Map.class);
    }

    // 3. 代码审查
    public Map<String, Object> reviewCode(String targetPath) throws Exception {
        Map<String, Object> payload = Map.of(
            "target_path", targetPath,
            "dimensions", new String[]{"complexity", "security"},
            "output_format", "json"
        );

        String jsonBody = objectMapper.writeValueAsString(payload);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_BASE + "/api/v1/review"))
            .header("X-API-Key", API_KEY)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        return objectMapper.readValue(response.body(), Map.class);
    }

    public static void main(String[] args) throws Exception {
        LingFlowClient client = new LingFlowClient();

        System.out.println("=== 列出技能 ===");
        Map<String, Object> skills = client.listSkills();
        System.out.println("找到 " + skills.get("total") + " 个技能");

        System.out.println("\n=== 执行技能 ===");
        Map<String, Object> params = Map.of(
            "prompt", "创建一个用户管理系统",
            "language", "java"
        );
        Map<String, Object> result = client.executeSkill("code-generation", params);
        System.out.println("成功: " + result.get("success"));

        System.out.println("\n=== 代码审查 ===");
        Map<String, Object> review = client.reviewCode("./src");
        System.out.println("总分: " + review.get("overall_score"));
    }
}
