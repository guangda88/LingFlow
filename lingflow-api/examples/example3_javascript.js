/**
 * 示例 3: JavaScript/Node.js 客户端
 */

const API_BASE = 'http://localhost:8000';
const API_KEY = 'dev-key-12345';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// 1. 列出技能
async function listSkills() {
  const response = await fetch(`${API_BASE}/api/v1/skills`, {
    method: 'GET',
    headers
  });
  return response.json();
}

// 2. 执行技能
async function executeSkill(skillName, params) {
  const response = await fetch(`${API_BASE}/api/v1/skills/${skillName}/execute`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      params,
      timeout: 300
    })
  });
  return response.json();
}

// 3. 运行工作流
async function runWorkflow(workflowId, params) {
  const response = await fetch(`${API_BASE}/api/v1/workflows/${workflowId}/run`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      params,
      strategy: 'hybrid'
    })
  });
  return response.json();
}

// 4. 代码审查
async function reviewCode(targetPath) {
  const response = await fetch(`${API_BASE}/api/v1/review`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      target_path: targetPath,
      dimensions: ['complexity', 'security'],
      output_format: 'json'
    })
  });
  return response.json();
}

// 5. GitHub 趋势
async function getGithubTrends(keywords) {
  const params = new URLSearchParams({
    keywords,
    language: 'python'
  });

  const response = await fetch(`${API_BASE}/api/v1/intelligence/github?${params}`, {
    method: 'GET',
    headers
  });
  return response.json();
}

// 使用示例
async function main() {
  try {
    console.log('=== 列出技能 ===');
    const skills = await listSkills();
    console.log(`找到 ${skills.total} 个技能`);

    console.log('\n=== 执行代码生成 ===');
    const result = await executeSkill('code-generation', {
      prompt: '创建一个用户管理系统',
      language: 'typescript'
    });
    console.log('成功:', result.success);

    console.log('\n=== 代码审查 ===');
    const review = await reviewCode('./src');
    console.log('总分:', review.overall_score);

  } catch (error) {
    console.error('错误:', error.message);
  }
}

// 运行
main();
