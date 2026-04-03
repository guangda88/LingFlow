"""
LingFlow Phase 4: 图表生成器

负责生成HTML和Chart.js图表。
"""

import json
from typing import Dict, Any, List


class ChartGenerator:
    """图表生成器

    生成各种优化相关的HTML图表。
    """

    def generate_progress_chart_data(self, trials: List[int], scores: List[float], best_score: float) -> Dict[str, Any]:
        """生成进度图表数据

        Args:
            trials: 试验ID列表
            scores: 分数列表
            best_score: 最佳分数

        Returns:
            图表数据字典
        """
        return {"trials": trials, "scores": scores, "bestScore": best_score}

    def generate_optimization_html(
        self,
        history: List,
        best_params: Dict[str, Any],
        best_score: float,
        convergence_rate: float,
        search_space: Dict[str, Any],
        metadata: Dict[str, Any],
        timestamp_readable: str,
    ) -> str:
        """生成优化报告HTML

        Args:
            history: 优化历史
            best_params: 最佳参数
            best_score: 最佳分数
            convergence_rate: 收敛率
            search_space: 搜索空间定义
            metadata: 元数据
            timestamp_readable: 可读时间戳

        Returns:
            完整的HTML字符串
        """
        # 提取历史数据
        scores = [t.score for t in history]
        trial_ids = list(range(1, len(history) + 1))

        # 生成JSON数据
        chart_data = {"trials": trial_ids, "scores": scores, "bestScore": best_score}

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LingFlow 参数优化报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 30px 0;
        }}
        .params-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .params-table th,
        .params-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .params-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .params-table tr:hover {{
            background: #f8f9fa;
        }}
        .convergence-indicator {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .converged {{
            background: #27ae60;
            color: white;
        }}
        .not-converged {{
            background: #e74c3c;
            color: white;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 LingFlow 参数优化报告</h1>

        <div class="summary">
            <div class="metric">
                <div class="metric-label">最佳分数</div>
                <div class="metric-value">{best_score:.4f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">试验次数</div>
                <div class="metric-value">{len(history)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">收敛率</div>
                <div class="metric-value">{convergence_rate:.1%}</div>
            </div>
            <div class="metric">
                <div class="metric-label">收敛状态</div>
                <div class="metric-value">
                    <span class="convergence-indicator {'converged' if convergence_rate > 0.9 else 'not-converged'}">
                        {'已收敛' if convergence_rate > 0.9 else '优化中'}
                    </span>
                </div>
            </div>
        </div>

        <h2>📈 优化进度</h2>
        <div class="chart-container">
            <canvas id="progressChart"></canvas>
        </div>

        <h2>🎯 最佳参数</h2>
        <table class="params-table">
            <thead>
                <tr>
                    <th>参数名</th>
                    <th>值</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
"""

        # 添加参数行
        for param_name, param_value in best_params.items():
            param_desc = search_space.get(param_name, {}).get("description", "")
            html += f"""
                <tr>
                    <td><code>{param_name}</code></td>
                    <td>{param_value}</td>
                    <td>{param_desc}</td>
                </tr>
"""

        html += (
            """
            </tbody>
        </table>

        <div class="timestamp">
            报告生成时间: """
            + timestamp_readable
            + """
        </div>
    </div>

    <script>
        const chartData = """
            + json.dumps(chart_data)
            + """;

        const ctx = document.getElementById('progressChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.trials,
                datasets: [{
                    label: '目标函数值',
                    data: chartData.scores,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }, {
                    label: '最佳值',
                    data: chartData.trials.map((_, i) => {
                        return Math.min(...chartData.scores.slice(0, i + 1));
                    }),
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '目标函数值'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '试验次数'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        )
        return html

    def generate_sensitivity_html(self, parameters: List[str], scores: List[float]) -> str:
        """生成敏感性分析HTML

        Args:
            parameters: 参数名列表
            scores: 敏感性分数列表

        Returns:
            完整的HTML字符串
        """
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>参数敏感性分析</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
        }}
        .chart-container {{
            position: relative;
            height: 500px;
            margin: 30px 0;
        }}
        .sensitivity-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .sensitivity-table th,
        .sensitivity-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .sensitivity-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .high {{
            background: #ffebee;
        }}
        .medium {{
            background: #fff3e0;
        }}
        .low {{
            background: #e8f5e8;
        }}
    </style>
</head>
<body>
    <h1>📊 参数敏感性分析</h1>

    <div class="chart-container">
        <canvas id="sensitivityChart"></canvas>
    </div>

    <h2>详细数据</h2>
    <table class="sensitivity-table">
        <thead>
            <tr>
                <th>参数</th>
                <th>敏感性分数</th>
                <th>级别</th>
            </tr>
        </thead>
        <tbody>
"""

        # 添加表格行
        scores_dict = dict(zip(parameters, scores))
        for param, score in sorted(scores_dict.items(), key=lambda x: -x[1]):
            level_class = "high" if score > 0.5 else ("medium" if score > 0.2 else "low")
            level_text = "高" if score > 0.5 else ("中" if score > 0.2 else "低")

            html += f"""
            <tr class="{level_class}">
                <td><code>{param}</code></td>
                <td>{score:.4f}</td>
                <td>{level_text}</td>
            </tr>
"""

        html += (
            """
        </tbody>
    </table>

    <script>
        const data = """
            + json.dumps({"labels": parameters, "scores": scores})
            + """;

        const ctx = document.getElementById('sensitivityChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: '敏感性分数',
                    data: data.scores,
                    backgroundColor: data.scores.map(s => {
                        if (s > 0.5) return 'rgba(231, 76, 60, 0.8)';
                        if (s > 0.2) return 'rgba(241, 196, 15, 0.8)';
                        return 'rgba(46, 204, 113, 0.8)';
                    }),
                    borderColor: data.scores.map(s => {
                        if (s > 0.5) return 'rgb(231, 76, 60)';
                        if (s > 0.2) return 'rgb(241, 196, 15)';
                        return 'rgb(46, 204, 113)';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        title: {
                            display: true,
                            text: '敏感性分数'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        )
        return html

    def generate_pareto_html(self, pareto_points: List, objective_names: List[str], all_evaluated: List) -> str:
        """生成Pareto前沿HTML

        Args:
            pareto_points: Pareto前沿点列表
            objective_names: 目标名称列表
            all_evaluated: 所有评估点

        Returns:
            完整的HTML字符串
        """
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pareto前沿分析</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
        }}
        .chart-container {{
            position: relative;
            height: 500px;
            margin: 30px 0;
        }}
        .solution-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .solution-table th,
        .solution-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .solution-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <h1>🎯 Pareto前沿分析</h1>
    <p>找到 {len(pareto_points)} 个非支配解</p>

    <div class="chart-container">
        <canvas id="paretoChart"></canvas>
    </div>

    <h2>Pareto前沿解</h2>
    <table class="solution-table">
        <thead>
            <tr>
                <th>#</th>
"""

        # 添加目标列
        for obj_name in objective_names:
            html += f"<th>{obj_name}</th>"
        html += "<th>聚合分数</th></tr></thead><tbody>"

        # 添加解行
        for i, point in enumerate(pareto_points):
            html += f"<tr><td>{i + 1}</td>"
            for obj_name in objective_names:
                obj_value = point.objectives.get(obj_name, 0)
                html += f"<td>{obj_value:.4f}</td>"
            html += f"<td>{point.aggregated_score:.4f}</td></tr>"

        html += (
            """
        </tbody>
    </table>

    <script>
        const paretoData = """
            + json.dumps(
                [
                    {
                        "x": point.objectives.get(objective_names[0], 0),
                        "y": point.objectives.get(objective_names[1], 0) if len(objective_names) > 1 else 0,
                        "objectives": point.objectives,
                    }
                    for point in pareto_points
                ]
            )
            + """;

        const ctx = document.getElementById('paretoChart').getContext('2d');
        new Chart(ctx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Pareto前沿',
                    data: paretoData.map(p => ({{x: p.x, y: p.y}})),
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }}, {{
                    label: '所有评估点',
                    data: """
            + json.dumps(
                [
                    {
                        "x": p.objectives.get(objective_names[0], 0),
                        "y": p.objectives.get(objective_names[1], 0) if len(objective_names) > 1 else 0,
                    }
                    for p in all_evaluated
                ]
            )
            + """,
                    backgroundColor: 'rgba(189, 195, 199, 0.3)',
                    borderColor: 'rgba(189, 195, 199, 0.5)',
                    pointRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const point = paretoData[context.dataIndex];
                                return '目标值: ' + JSON.stringify(point.objectives);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: '{objective_names[0] if objective_names else "目标1"}'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: '{objective_names[1] if len(objective_names) > 1 else "目标2"}'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        )
        return html
