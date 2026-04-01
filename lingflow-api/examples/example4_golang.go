package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	APIBase  = "http://localhost:8000"
	APIKey   = "dev-key-12345"
)

// 1. 列出技能
func listSkills() (map[string]interface{}, error) {
	req, _ := http.NewRequest("GET", APIBase+"/api/v1/skills", nil)
	req.Header.Set("X-API-Key", APIKey)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

// 2. 执行技能
func executeSkill(skillName string, params map[string]interface{}) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"params":   params,
		"timeout":  300,
	}

	jsonData, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", APIBase+"/api/v1/skills/"+skillName+"/execute", bytes.NewReader(jsonData))
	req.Header.Set("X-API-Key", APIKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

// 3. 代码审查
func reviewCode(targetPath string) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"target_path":   targetPath,
		"dimensions":    []string{"complexity", "security"},
		"output_format": "json",
	}

	jsonData, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", APIBase+"/api/v1/review", bytes.NewReader(jsonData))
	req.Header.Set("X-API-Key", APIKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

func main() {
	fmt.Println("=== 列出技能 ===")
	skills, _ := listSkills()
	fmt.Printf("找到 %v 个技能\n", skills["total"])

	fmt.Println("\n=== 执行技能 ===")
	result, _ := executeSkill("code-generation", map[string]interface{}{
		"prompt":   "创建一个 REST API",
		"language": "go",
	})
	fmt.Printf("成功: %v\n", result["success"])

	fmt.Println("\n=== 代码审查 ===")
	review, _ := reviewCode("./src")
	fmt.Printf("总分: %v\n", review["overall_score"])
}
